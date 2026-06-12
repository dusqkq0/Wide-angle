#!/usr/bin/env python3
"""쿠팡 파트너스 API로 성분별 추천 상품을 검색해 data/products.json을 자동으로 채운다.

⚠️ 쿠팡을 직접 크롤링하는 것이 아니라, 쿠팡 파트너스 '공식 API'를 사용합니다.
   - 합법적이며, 받아오는 상품 링크에 내 추적코드가 포함되어 수익으로 연결됩니다.
   - 직접 크롤링은 약관 위반이고 추적코드가 없어 수익이 발생하지 않습니다.

준비:
  1. partners.coupang.com 가입·승인
  2. 상단 메뉴 Tools → 파트너스 API 에서 ACCESS KEY / SECRET KEY 발급
  3. 환경변수로 키 설정 후 실행:
       pip install requests --break-system-packages
       export COUPANG_ACCESS_KEY=발급키
       export COUPANG_SECRET_KEY=발급시크릿
       python coupang_fetch.py --ingredients niacinamide hyaluronic-acid retinol --per 2

동작:
  - 지정한 성분(없으면 기본 대표 성분)의 한글명으로 쿠팡 상품을 검색
  - 상위 결과를 data/products.json에 status="draft"로 병합 (기존 항목은 보존)
  - 검토 후 좋은 제품만 status를 "active"로 바꾸면 사이트에 노출됨

※ 샌드박스 환경에서는 api-gateway.coupang.com 접근이 막혀 있을 수 있습니다.
  본인 컴퓨터(또는 서버)에서 실행하세요.
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import requests

BASE = Path(__file__).parent
PRODUCTS_PATH = BASE / "data/products.json"
INGREDIENTS_PATH = BASE / "data/ingredients.json"

DOMAIN = "https://api-gateway.coupang.com"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"

# 검색할 기본 대표 성분 (id). --ingredients로 직접 지정하면 이 목록 대신 사용.
DEFAULT_INGREDIENTS = [
    "niacinamide", "hyaluronic-acid", "retinol", "ascorbic-acid", "ceramide",
    "panthenol", "centella", "madecassoside", "salicylic-acid", "glycolic-acid",
    "propolis", "green-tea", "squalane", "bakuchiol", "zinc-oxide",
    "arbutin", "tranexamic-acid", "collagen", "glycerin", "azelaic-acid",
]


def hmac_auth(method: str, path: str, query: str, access: str, secret: str) -> str:
    """쿠팡 Open API HMAC 서명 (공식 문서 방식)."""
    dt = time.strftime("%y%m%d", time.gmtime()) + "T" + time.strftime("%H%M%S", time.gmtime()) + "Z"
    message = dt + method + path + query
    signature = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access}, signed-date={dt}, signature={signature}"


def search(keyword: str, limit: int, access: str, secret: str) -> list[dict]:
    """쿠팡 파트너스 상품 검색 API 호출."""
    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit})
    auth = hmac_auth("GET", SEARCH_PATH, query, access, secret)
    url = f"{DOMAIN}{SEARCH_PATH}?{query}"
    r = requests.get(url, headers={
        "Authorization": auth,
        "Content-Type": "application/json;charset=UTF-8",
    }, timeout=30)
    r.raise_for_status()
    body = r.json()
    if str(body.get("rCode")) not in ("0", "200"):
        print(f"  [경고] '{keyword}' 응답 코드 {body.get('rCode')}: {body.get('rMessage')}")
    return body.get("data", {}).get("productData", []) or []


def won(price) -> str:
    try:
        return f"{int(price):,}원"
    except (ValueError, TypeError):
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingredients", nargs="*", help="검색할 성분 id 목록 (기본: 대표 성분)")
    ap.add_argument("--per", type=int, default=2, help="성분당 가져올 상품 수 (기본 2)")
    ap.add_argument("--activate", action="store_true",
                    help="가져온 제품을 바로 active로 (기본은 draft — 검토 후 수동 활성화 권장)")
    args = ap.parse_args()

    access = os.environ.get("COUPANG_ACCESS_KEY")
    secret = os.environ.get("COUPANG_SECRET_KEY")
    if not access or not secret:
        sys.exit("환경변수 COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 를 설정하세요.")

    ingredients = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))["ingredients"]
    ing_by_id = {i["id"]: i for i in ingredients}
    targets = args.ingredients or DEFAULT_INGREDIENTS

    pdata = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in pdata["products"]}
    existing_urls = {p.get("url") for p in pdata["products"] if p.get("url")}
    added = 0

    for ing_id in targets:
        ing = ing_by_id.get(ing_id)
        if not ing:
            print(f"  [건너뜀] 알 수 없는 성분 id: {ing_id}")
            continue
        keyword = ing["korean_name"]
        # 이 성분에 'good'인 피부타입을 제품 태그로
        skin = [t for t, v in ing.get("skin_types", {}).items() if v == "good"]
        try:
            results = search(keyword, args.per, access, secret)
        except Exception as e:
            print(f"  [경고] '{keyword}' 검색 실패: {e}")
            continue

        for p in results:
            pid = f"coupang-{p.get('productId')}"
            url = p.get("productUrl", "")
            if pid in existing_ids or url in existing_urls or not url:
                continue
            pdata["products"].append({
                "id": pid,
                "name": p.get("productName", "")[:80],
                "url": url,                       # 추적코드 포함 파트너스 링크
                "image": p.get("productImage", ""),
                "price": won(p.get("productPrice")),
                "note": f"{ing['korean_name']} 관련 추천 (쿠팡)",
                "ingredients": [ing_id],
                "skin_types": skin,
                "status": "active" if args.activate else "draft",
            })
            existing_ids.add(pid)
            existing_urls.add(url)
            added += 1
        print(f"  · {keyword}: {len(results)}건 조회")
        time.sleep(0.6)  # rate limit 여유

    PRODUCTS_PATH.write_text(json.dumps(pdata, ensure_ascii=False, indent=2), encoding="utf-8")
    state = "active" if args.activate else "draft"
    print(f"\n[OK] 신규 상품 {added}건을 products.json에 {state}로 추가")
    print("  → 검토 후(또는 바로) 페이지 재생성: python generate_page.py --base-url https://merry-gelato-2a6bc1.netlify.app/")


if __name__ == "__main__":
    main()
