#!/usr/bin/env python3
"""신규 화장품 성분 자동 수집기.

공식 데이터 출처에서 성분 목록을 받아와 기존 data/ingredients.json과 비교,
새로운 성분을 'draft' 상태로 추가한 뒤 페이지를 재생성합니다.

지원 출처
1. 식약처 화장품 원료성분정보 (공공데이터포털, 무료 API 키 필요)
   https://www.data.go.kr/data/15111774/openapi.do
2. EU CosIng 검색 API (가입·키 발급 불필요, 약 36,000건)
   https://ec.europa.eu/growth/tools-databases/cosing/

사용법:
    pip install requests --break-system-packages

    # 인기 성분 위주로 수집 (권장) — 미리 정의된 인기 키워드 목록으로 검색
    MFDS_API_KEY=발급키 python crawler.py --source mfds --popular
    python crawler.py --source cosing --popular

    # 특정 검색어로 수집
    MFDS_API_KEY=발급키 python crawler.py --source mfds --query 히알루로닉 --limit 20
    python crawler.py --source cosing --query niacinamide --limit 20

    # 전체에서 순서대로 수집 (인기도와 무관)
    MFDS_API_KEY=발급키 python crawler.py --source mfds --limit 50

새로 추가된 성분은 status="draft"로 저장되며 페이지에는 노출되지 않습니다.
설명·피부타입 정보를 채우고 status를 "published"로 바꾸면 게시됩니다.
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests

BASE = Path(__file__).parent
DATA_PATH = BASE / "data/ingredients.json"

# 스킨케어에서 수요가 높은 인기 성분 키워드.
# 식약처(한글)·CosIng(영문) 각각에 맞는 검색어를 함께 둔다.
# 키워드 하나로 파생 성분(○○유도체, ○○염 등)까지 함께 잡힌다.
# 주의: 식약처 표준명은 외래어를 "하이-/-이-" 식으로 표기한다
#       (예: 히알루론산 → "하이알루로닉", 글리콜릭 → "글라이콜릭").
POPULAR_QUERIES = [
    ("하이알루로닉", "hyaluron"),     # 히알루론산 계열
    ("나이아신아마이드", "niacinamide"),
    ("레티놀", "retinol"),
    ("레티날", "retinal"),
    ("아스코빌", "ascorb"),           # 비타민C 유도체
    ("아스코빅", "ascorbic"),         # 순수 비타민C
    ("토코페롤", "tocopher"),         # 비타민E
    ("세라마이드", "ceramide"),
    ("펩타이드", "peptide"),
    ("콜라겐", "collagen"),
    ("판테놀", "panthenol"),
    ("아데노신", "adenosine"),
    ("센텔라", "centella"),
    ("마데카", "madecass"),
    ("알란토인", "allantoin"),
    ("알부틴", "arbutin"),
    ("트라넥사믹", "tranexamic"),
    ("아젤라", "azelaic"),            # 식약처: 아젤라마이드 등
    ("살리실릭", "salicylic"),
    ("글라이콜릭", "glycolic"),
    ("락토바실러스", "lactobacillus"),  # 발효
    ("프로폴리스", "propolis"),
    ("녹차", "camellia sinensis"),
    ("약모밀", "houttuynia"),         # 어성초의 식약처 표준명
    ("병풀", "centella"),
    ("스쿠알란", "squalane"),
    ("바쿠치올", "bakuchiol"),
    ("카페인", "caffeine"),
    ("징크옥사이드", "zinc oxide"),
    ("글리세린", "glycerin"),
]

DRAFT_TEMPLATE = {
    "category": "미분류",
    "description": "(설명 작성 필요 — draft 상태)",
    "benefits": [],
    "skin_types": {"건성": "caution", "지성": "caution", "민감성": "caution",
                   "복합성": "caution", "여드름성": "caution"},
    "safety_grade": 5,
    "cautions": "신규 수집 성분 — 검토 전입니다.",
    "status": "draft",
}


def norm(name: str) -> str:
    """INCI명 비교용 정규화."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "unknown"


MFDS_URL = "https://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"


def fetch_mfds(api_key: str, limit: int, query: str = "") -> list[dict]:
    """식약처 화장품 원료성분정보 API.

    query가 주어지면 한글 성분명(INGR_KOR_NAME)으로 부분검색한다.
    """
    items, page = [], 1
    while len(items) < limit:
        params = {
            "serviceKey": api_key, "type": "json",
            "pageNo": page, "numOfRows": min(100, limit - len(items)),
        }
        if query:
            params["INGR_KOR_NAME"] = query
        r = requests.get(MFDS_URL, params=params, timeout=30)
        r.raise_for_status()
        body = r.json().get("body", {})
        rows = body.get("items") or []
        if not rows:
            break
        for row in rows:
            row = row.get("item", row)
            items.append({
                "korean_name": row.get("INGR_KOR_NAME") or "",
                "inci_name": row.get("INGR_ENG_NAME") or "",
                "chemical_description": row.get("ORIGIN_MAJOR_KOR_NAME") or "",
                "cas_no": row.get("CAS_NO") or "",
                "source": "식약처 원료성분정보",
            })
        page += 1
    return items[:limit]


def fetch_popular(source: str, api_key: str = "", per_query: int = 10) -> list[dict]:
    """인기 성분 키워드 목록을 순회하며 수집해 합친다."""
    seen, collected = set(), []
    for kor, eng in POPULAR_QUERIES:
        try:
            if source == "mfds":
                batch = fetch_mfds(api_key, per_query, query=kor)
            else:
                batch = fetch_cosing(per_query, query=eng)
        except Exception as e:  # 키워드 하나가 실패해도 나머지는 계속
            print(f"  [경고] '{kor or eng}' 수집 실패: {e}")
            continue
        new = 0
        for it in batch:
            k = norm(it["inci_name"])
            if k and k not in seen:
                seen.add(k)
                collected.append(it)
                new += 1
        print(f"  · {kor or eng}: {len(batch)}건 조회 → {new}건 누적")
    return collected


COSING_API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
COSING_API_KEY = "285a77fd-1257-4271-8507-f0c6b2961203"  # CosIng 웹사이트가 쓰는 공개 키


def fetch_cosing(limit: int, query: str = "*") -> list[dict]:
    """EU CosIng 공식 검색 API (별도 가입·키 발급 불필요).

    구 CSV 데이터셋은 data.europa.eu에서 삭제되어, 현재 CosIng 웹사이트가
    사용하는 EC Search API를 직접 호출한다. 전체 약 36,000건.
    """
    items, page = [], 1
    while len(items) < limit:
        r = requests.post(COSING_API, params={
            "apiKey": COSING_API_KEY, "text": query,
            "pageSize": min(100, limit - len(items)), "pageNumber": page,
        }, timeout=60)
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            break
        for res in results:
            m = res.get("metadata", {})

            def first(key):
                v = m.get(key) or []
                return v[0] if v else ""

            inci = first("inciName") or first("nameOfCommonIngredientsGlossary")
            if not inci:
                continue
            items.append({
                "korean_name": inci,  # 한글명은 검토 단계에서 입력
                "inci_name": inci,
                "chemical_description": first("chemicalDescription"),
                "functions": m.get("functionName") or [],
                "cas_no": first("casNo"),
                "source": "EU CosIng",
            })
        page += 1
    return items[:limit]


def merge(new_items: list[dict]) -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = {norm(i["inci_name"]) for i in data["ingredients"]}
    existing_ids = {i["id"] for i in data["ingredients"]}
    added = 0
    for item in new_items:
        key = norm(item["inci_name"])
        if not key or key in existing:
            continue
        entry_id = slug(item["inci_name"])
        if entry_id in existing_ids:
            entry_id += f"-{added}"
        entry = {
            "id": entry_id,
            "korean_name": item["korean_name"] or item["inci_name"],
            "inci_name": item["inci_name"],
            **DRAFT_TEMPLATE,
            "source": item.get("source", ""),
            "added_date": date.today().isoformat(),
        }
        # CosIng이 제공하는 참고 정보가 있으면 검수용으로 같이 저장
        if item.get("chemical_description"):
            entry["description"] = f"(검토 필요) {item['chemical_description']}"
        if item.get("functions"):
            entry["benefits"] = item["functions"][:4]
        if item.get("cas_no"):
            entry["cas_no"] = item["cas_no"]
        data["ingredients"].append(entry)
        existing.add(key)
        existing_ids.add(entry_id)
        added += 1
    data["meta"]["updated"] = date.today().isoformat()
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return added


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mfds", "cosing"], default="mfds")
    ap.add_argument("--limit", type=int, default=50, help="이번 실행에서 수집할 최대 개수")
    ap.add_argument("--query", default="", help="검색어 (식약처는 한글, CosIng은 영문)")
    ap.add_argument("--popular", action="store_true",
                    help="인기 성분 키워드 목록으로 수집 (권장)")
    ap.add_argument("--per-query", type=int, default=10,
                    help="--popular 사용 시 키워드당 수집 개수")
    ap.add_argument("--no-build", action="store_true", help="페이지 재생성 생략")
    args = ap.parse_args()

    key = ""
    if args.source == "mfds":
        key = os.environ.get("MFDS_API_KEY")
        if not key:
            sys.exit("MFDS_API_KEY 환경변수에 공공데이터포털 인증키를 설정하세요.")

    if args.popular:
        print(f"인기 성분 {len(POPULAR_QUERIES)}개 키워드로 수집 중...")
        items = fetch_popular(args.source, key, args.per_query)
    elif args.source == "mfds":
        items = fetch_mfds(key, args.limit, query=args.query)
    else:
        items = fetch_cosing(args.limit, args.query or "*")

    added = merge(items)
    print(f"[OK] 수집 {len(items)}건 중 신규 {added}건을 draft로 추가")

    if not args.no_build:
        from generate_page import generate, generate_quiz, generate_details
        n = generate(DATA_PATH, BASE / "template.html", BASE / "index.html")
        print(f"[OK] index.html 재생성 — 게시 성분 {n}개 (draft 제외)")
        quiz_tpl = BASE / "quiz_template.html"
        if quiz_tpl.exists():
            generate_quiz(DATA_PATH, quiz_tpl, BASE / "quiz.html")
            print(f"[OK] quiz.html 진단 퀴즈 재생성")
        an_tpl = BASE / "analyzer_template.html"
        if an_tpl.exists():
            generate_quiz(DATA_PATH, an_tpl, BASE / "analyzer.html")
            print(f"[OK] analyzer.html 전성분 분석기 재생성")
        combos_tpl = BASE / "combos_template.html"
        if combos_tpl.exists():
            generate_quiz(DATA_PATH, combos_tpl, BASE / "combos.html")
            print(f"[OK] combos.html 궁합 체크 재생성")
        avoid_tpl = BASE / "avoid_template.html"
        if avoid_tpl.exists():
            generate_quiz(DATA_PATH, avoid_tpl, BASE / "avoid.html")
            print(f"[OK] avoid.html 상황별 회피 필터 재생성")
        from generate_page import generate_result_pages
        generate_result_pages(DATA_PATH, BASE, base_url="")
        generate_details(DATA_PATH, BASE, base_url="")
        print(f"[OK] result/·detail/ 페이지 + sitemap.xml 재생성 (제휴 제품 포함)")
