#!/usr/bin/env python3
"""draft 성분 29개에 고객용 설명/효능/피부타입/안전등급/주의사항을 채우고 published 전환."""
import json
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data/ingredients.json"

G = {"건성": "good", "지성": "good", "민감성": "good", "복합성": "good", "여드름성": "good"}


def st(d=None):
    s = dict(G)
    if d:
        s.update(d)
    return s


# id -> {category, description, benefits, skin_types, safety_grade, cautions}
ENRICH = {
    "solanum-melongena-eggplant-fruit-extract": {
        "category": "항산화", "benefits": ["항산화", "보습", "진정"],
        "description": "가지 열매에서 얻은 추출물. 안토시아닌 등 항산화 성분이 풍부해 외부 자극으로부터 피부를 보호하고 수분을 더해줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "agarum-cribrosum-extract": {
        "category": "보습", "benefits": ["수분 공급", "미네랄 공급", "진정"],
        "description": "구멍쇠미역(해조류)에서 추출한 성분. 바다 유래 미네랄과 다당류가 피부에 수분을 채우고 매끄럽게 가꿔줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "lupine-amino-acids": {
        "category": "보습·탄력", "benefits": ["보습", "탄력 보조", "피부 컨디셔닝"],
        "description": "루핀콩 단백질을 잘게 분해해 얻은 아미노산 혼합물. 피부 구성 성분과 닮아 흡수가 잘 되고 탄력·보습을 돕습니다.",
        "skin_types": st({"민감성": "caution"}), "safety_grade": 1,
        "cautions": "콩(두류) 알레르기가 있다면 패치 테스트 권장."},
    "leucine": {
        "category": "보습·컨디셔닝", "benefits": ["피부 컨디셔닝", "보습 보조"],
        "description": "필수 아미노산의 하나로, 제형을 부드럽게 하고 피부 표면을 매끄럽게 정돈하는 보조 성분입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "leuconostoc-radish-root-ferment-filtrate": {
        "category": "발효·보존 보조", "benefits": ["천연 보존 보조", "보습", "진정"],
        "description": "무 뿌리를 유산균(류코노스톡)으로 발효해 거른 성분. 제품을 자연스럽게 신선하게 유지하면서 순하게 수분을 더해 무방부 콘셉트 제품에 자주 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "leukocyte-extract": {
        "category": "재생·영양", "benefits": ["재생 보조", "영양 공급"],
        "description": "면역세포(백혈구)에서 유래한 단백질 성분으로, 피부의 회복과 영양 공급을 돕는 목적으로 소량 배합됩니다.",
        "skin_types": st({"민감성": "caution"}), "safety_grade": 2,
        "cautions": "동물 유래 성분. 비건 제품을 찾는다면 확인이 필요합니다."},
    "rhinacanthus-communis-extract": {
        "category": "진정·트러블", "benefits": ["진정", "항균 보조", "트러블 완화"],
        "description": "동남아에서 약용으로 쓰이는 식물 추출물. 자극받은 피부를 달래고 트러블 케어를 보조합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "linalool": {
        "category": "주의 성분 (향료)", "benefits": ["향 부여"],
        "description": "라벤더 등 많은 식물에 들어 있는 천연 향 성분. 은은한 향을 더하지만 공기 중에서 산화되면 알레르기를 유발할 수 있어 EU가 표기를 의무화한 향료 26종 중 하나입니다.",
        "skin_types": st({"민감성": "bad", "여드름성": "caution", "건성": "caution", "지성": "caution", "복합성": "caution"}),
        "safety_grade": 6, "cautions": "향료 알레르기·민감성 피부는 주의. 무향 제품을 권장합니다."},
    "linalyl-acetate": {
        "category": "주의 성분 (향료)", "benefits": ["향 부여"],
        "description": "베르가못·라벤더 향의 핵심이 되는 향 성분. 향을 부드럽게 내지만 향료 민감성 피부에는 자극이 될 수 있습니다.",
        "skin_types": st({"민감성": "bad", "건성": "caution", "지성": "caution", "복합성": "caution", "여드름성": "caution"}),
        "safety_grade": 4, "cautions": "향료 민감성 피부는 주의."},
    "linolenic-acid": {
        "category": "장벽·진정", "benefits": ["피부 장벽 강화", "진정", "수분 손실 방지"],
        "description": "들기름·아마씨 등에 풍부한 오메가-3 계열 필수지방산. 피부 장벽을 채워 수분을 지키고 붉어진 피부를 진정시킵니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "linoleamide-mea": {
        "category": "점도·사용감 조절", "benefits": ["점도 조절", "거품 안정", "사용감 개선"],
        "description": "지방산에서 유래한 성분으로, 주로 클렌저·샴푸에서 거품을 안정시키고 제형의 점도를 잡아주는 역할을 합니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "특별한 주의사항 없음."},
    "abies-koreana-leaf-powder": {
        "category": "각질·향", "benefits": ["부드러운 각질 케어", "은은한 향", "청량감"],
        "description": "한국 특산 구상나무 잎을 곱게 간 가루. 부드러운 물리적 스크럽과 숲 향의 청량감을 더해줍니다.",
        "skin_types": st({"민감성": "caution", "여드름성": "caution"}), "safety_grade": 1,
        "cautions": "물리적 알갱이가 있어 민감성·트러블 피부는 강하게 문지르지 않도록 주의."},
    "linoleamidopropyl-dimethylamine-dimer-dilinoleate": {
        "category": "헤어·컨디셔닝", "benefits": ["모발 컨디셔닝", "정전기 방지", "부드러움"],
        "description": "지방산에서 유래한 컨디셔닝 성분으로, 주로 헤어 제품에서 모발을 매끄럽고 차분하게 정돈합니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "주로 헤어 제품용 성분."},
    "linoleamidopropyl-ethyldimonium-ethosulfate": {
        "category": "헤어·컨디셔닝", "benefits": ["모발 컨디셔닝", "정전기 방지"],
        "description": "양이온성 컨디셔닝 성분. 모발 표면에 부드럽게 흡착해 엉킴과 정전기를 줄여줍니다.",
        "skin_types": st(), "safety_grade": 3, "cautions": "주로 헤어 제품용 성분."},
    "linoleamidopropyl-pg-dimonium-chloride-phosphate": {
        "category": "헤어·컨디셔닝", "benefits": ["모발 컨디셔닝", "보습", "정전기 방지"],
        "description": "지방산 유래 컨디셔닝 성분으로, 모발과 두피에 순하게 수분감과 매끄러움을 더합니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "주로 헤어 제품용 성분."},
    "linoleamidopropyl-pg-dimonium-chloride-phosphate-dimethicone": {
        "category": "헤어·컨디셔닝", "benefits": ["모발 컨디셔닝", "윤기 부여"],
        "description": "위 컨디셔닝 성분에 실리콘(다이메티콘)을 결합한 형태로, 모발에 윤기와 매끄러운 코팅감을 줍니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "주로 헤어 제품용 성분."},
    "linoleic-acid": {
        "category": "장벽·트러블", "benefits": ["피부 장벽 강화", "여드름 완화 보조", "수분 손실 방지"],
        "description": "해바라기씨유 등에 풍부한 오메가-6 필수지방산. 피부 장벽의 핵심 구성 성분으로, 특히 피지의 리놀레익애씨드가 부족한 여드름 피부에 도움을 줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "phaseolus-lunatus-green-bean-seed-extract": {
        "category": "보습·탄력", "benefits": ["보습", "탄력 보조", "진정"],
        "description": "리마콩 씨에서 얻은 추출물. 단백질·아미노산이 풍부해 피부에 영양과 탄력을 더합니다.",
        "skin_types": st({"민감성": "caution"}), "safety_grade": 1,
        "cautions": "콩(두류) 알레르기가 있다면 패치 테스트 권장."},
    "limonene": {
        "category": "주의 성분 (향료)", "benefits": ["향 부여"],
        "description": "감귤류 껍질에 풍부한 상큼한 향 성분. 향을 더하지만 산화되면 자극·알레르기를 유발할 수 있어 EU 표기 의무 향료 26종에 포함됩니다.",
        "skin_types": st({"민감성": "bad", "여드름성": "caution", "건성": "caution", "지성": "caution", "복합성": "caution"}),
        "safety_grade": 6, "cautions": "향료 알레르기·민감성 피부는 주의. 무향 제품을 권장합니다."},
    "limonia-acidissima-wood-powder": {
        "category": "각질·향", "benefits": ["부드러운 각질 케어", "은은한 향"],
        "description": "우드애플 나무의 목부를 곱게 간 가루. 가벼운 물리적 각질 케어와 우디 향을 더합니다.",
        "skin_types": st({"민감성": "caution", "여드름성": "caution"}), "safety_grade": 1,
        "cautions": "물리적 알갱이가 있어 민감성·트러블 피부는 강하게 문지르지 않도록 주의."},
    "riboflavin-lactoflavin": {
        "category": "항산화·착색", "benefits": ["항산화", "자연 착색", "컨디셔닝"],
        "description": "비타민B2. 항산화 작용을 하며 제품에 은은한 노란빛을 더하는 천연 착색 역할도 합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "노란색을 띠어 제형 색에 영향을 줄 수 있음."},
    "abies-koreana-leaf-extract": {
        "category": "진정·항산화", "benefits": ["진정", "항산화", "수렴"],
        "description": "구상나무 잎에서 추출한 성분. 피톤치드 계열 성분이 피부를 진정시키고 항산화로 보호합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "litsea-cubeba-fruit-oil": {
        "category": "주의 성분 (에센셜오일)", "benefits": ["향 부여", "항균 보조"],
        "description": "리씨(May Chang) 열매에서 추출한 레몬 향 에센셜오일. 상쾌한 향과 항균 효과가 있지만 농도가 높으면 자극이 될 수 있습니다.",
        "skin_types": st({"민감성": "bad", "건성": "caution", "여드름성": "caution"}), "safety_grade": 4,
        "cautions": "정유 성분으로 민감성 피부는 주의. 광과민 가능성이 있어 사용 후 자외선 노출에 유의."},
    "litchi-chinensis-pericarp-extract": {
        "category": "항산화", "benefits": ["항산화", "톤 개선 보조", "진정"],
        "description": "리치 껍질 추출물. 폴리페놀 항산화 성분이 풍부해 피부를 보호하고 환한 톤을 돕습니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "litchi-chinensis-seed-extract": {
        "category": "항산화·보습", "benefits": ["항산화", "보습", "탄력 보조"],
        "description": "리치 씨에서 얻은 추출물로, 항산화와 함께 피부에 수분과 탄력을 더해줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "litchi-chinensis-fruit-extract": {
        "category": "항산화·보습", "benefits": ["항산화", "수분 공급", "영양 공급"],
        "description": "리치 과육 추출물. 비타민C 등 영양 성분이 풍부해 피부에 생기와 수분을 더합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "lithothamnion-calcareum-powder": {
        "category": "미네랄·보습", "benefits": ["미네랄 공급", "보습", "피부 정돈"],
        "description": "칼슘·마그네슘이 풍부한 홍조류를 갈아 만든 가루. 미네랄을 공급하고 피부 표면을 매끄럽게 정돈합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "lithium-magnesium-sodium-silicate": {
        "category": "점증·흡착", "benefits": ["점도 조절", "피지 흡착", "제형 안정"],
        "description": "합성 점토 성분으로, 제형을 안정적으로 굳혀주고 과잉 피지를 흡착하는 역할을 합니다. 마스크·클레이 제품에 자주 쓰입니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "특별한 주의사항 없음."},
    "lithium-stearate": {
        "category": "점도·사용감 조절", "benefits": ["점도 조절", "사용감 개선"],
        "description": "지방산(스테아릭애씨드)의 리튬염으로, 제형의 점도와 발림성을 조절하는 보조 성분입니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "특별한 주의사항 없음."},
}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    filled = 0
    for ing in data["ingredients"]:
        e = ENRICH.get(ing["id"])
        if not e or ing.get("status") != "draft":
            continue
        ing.update(e)
        ing["status"] = "published"
        ing.pop("source", None)
        filled += 1
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    remaining = [i["id"] for i in data["ingredients"] if i.get("status") == "draft"]
    print(f"{filled}개 성분 작성·게시 완료. 남은 draft: {len(remaining)}개")
    if remaining:
        print("미처리:", remaining)


if __name__ == "__main__":
    main()
