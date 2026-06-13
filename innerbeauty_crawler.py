#!/usr/bin/env python3
"""이너뷰티(건강기능식품) 성분 자동 수집기 — 화장품 크롤러와 분리.

식약처 '건강기능식품 영양DB'(식품안전나라 OpenAPI, 서비스ID I0760)에서 원료(성분) 정보를
받아와 data/innerbeauty.json에 'draft'로 병합한다. (화장품 ingredients.json은 건드리지 않음)

데이터: 건강기능식품 영양DB
  - 공공데이터포털: https://www.data.go.kr/data/15085712/openapi.do
  - 실제 서비스: 식품안전나라 OpenAPI (https://openapi.foodsafetykorea.go.kr)
  - 호출 형식: https://openapi.foodsafetykorea.go.kr/api/{인증키}/I0760/json/{시작}/{끝}
  - 주요 필드: HELT_ITM_GRP_NM(원료명), MLSFC_NM/SCLAS_NM(분류), HELT_ITM_GRP_CD(코드)

⚠️ 이 키는 화장품 키(MFDS_API_KEY)와 별개입니다.

사용법:
    pip install requests --break-system-packages
    export HFOOD_API_KEY=발급받은키
    python innerbeauty_crawler.py --limit 100

신규 원료는 status="draft"로 들어오며 페이지·추천에 노출되지 않습니다.
설명·기능성·skin_types를 검토·작성한 뒤 status를 "published"로 바꾸면 노출됩니다.
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
DATA_PATH = BASE / "data/innerbeauty.json"
API_BASE = "https://openapi.foodsafetykorea.go.kr/api"
SERVICE_ID = "I0760"  # 건강기능식품 영양DB

# 신규 원료 기본값 (검수 전 상태). 화장품과 달리 안전등급(EWG) 없음.
DRAFT_TEMPLATE = {
    "category": "미분류",
    "description": "(설명 작성 필요 — draft 상태)",
    "benefits": [],
    "skin_types": {"건성": "good", "지성": "good", "민감성": "good", "복합성": "good", "여드름성": "good"},
    "daily_intake": "제품 표시 섭취량을 따르세요.",
    "functional": "기능성 인정 범위 확인 필요",
    "caution": "신규 수집 원료 — 검토 전입니다. 기능성 표현은 인정 범위 내에서만 기재하세요.",
    "status": "draft",
}

def norm(s): return re.sub(r"[^a-z0-9가-힣]", "", (s or "").lower())
def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "item"


def fetch(api_key, limit):
    """식품안전나라 건강기능식품 영양DB(I0760) 호출. 1회 최대 100건씩 페이징."""
    items, start = [], 1
    while len(items) < limit:
        end = start + min(100, limit - len(items)) - 1
        url = f"{API_BASE}/{api_key}/{SERVICE_ID}/json/{start}/{end}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        block = r.json().get(SERVICE_ID, {})
        result = block.get("RESULT", {})
        if result.get("CODE") and result["CODE"] != "INFO-000":
            raise RuntimeError(f"{result.get('CODE')}: {result.get('MSG')}")
        rows = block.get("row") or []
        if not rows:
            break
        for row in rows:
            kor = row.get("HELT_ITM_GRP_NM", "").strip()
            if not kor:
                continue
            items.append({
                "korean_name": kor,
                "eng_name": "",
                "mlsfc": row.get("MLSFC_NM") or row.get("SCLAS_NM") or "",  # 분류(개별인정형 등)
                "code": row.get("HELT_ITM_GRP_CD", ""),
            })
        start = end + 1
    return items[:limit]


def merge(new_items):
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = {norm(i["korean_name"]) for i in data["ingredients"]}
    existing_ids = {i["id"] for i in data["ingredients"]}
    added = 0
    for it in new_items:
        key = norm(it["korean_name"])
        if not key or key in existing:
            continue
        iid = slug(it.get("eng_name") or it["korean_name"])
        if iid in existing_ids:
            iid += f"-{added}"
        entry = {
            "id": iid,
            "korean_name": it["korean_name"],
            "eng_name": it.get("eng_name", ""),
            **DRAFT_TEMPLATE,
            "source": "식약처 건강기능식품 영양DB",
            "added_date": date.today().isoformat(),
        }
        if it.get("mlsfc"):
            entry["functional"] = f"{it['mlsfc']} (인정 범위 확인 필요)"
        data["ingredients"].append(entry)
        existing.add(key); existing_ids.add(iid); added += 1
    data["meta"]["updated"] = date.today().isoformat()
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return added


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="수집할 최대 원료 수 (영양DB 총 585건)")
    args = ap.parse_args()

    key = os.environ.get("HFOOD_API_KEY")
    if not key:
        sys.exit("환경변수 HFOOD_API_KEY 에 건강기능식품 영양DB 인증키를 설정하세요. (화장품 키와 별개)")

    try:
        items = fetch(key, args.limit)
    except Exception as e:
        sys.exit(f"수집 실패: {e}")

    added = merge(items)
    print(f"[OK] 수집 {len(items)}건 중 신규 {added}건을 innerbeauty.json에 draft로 추가")
    print("  → 검수(설명·기능성·skin_types 작성) 후 status를 published로 바꾸세요.")
    if items and not added:
        print("  (모두 기존 데이터와 중복입니다)")
