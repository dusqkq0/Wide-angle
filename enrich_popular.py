#!/usr/bin/env python3
"""인기 키워드 draft 중 '대표 성분'만 골라 고객용 정보를 채우고 published 전환.
파생염·유도체·발효물 등은 draft로 남긴다."""
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


# id(=INCI slug) -> 고객용 정보
ENRICH = {
    "hyaluronic-acid": {
        "category": "보습", "benefits": ["수분 공급", "피부 장벽 강화", "탄력 보조"],
        "description": "피부 속 수분을 끌어당겨 머금는 대표 보습 성분. 자기 무게의 수백 배에 달하는 물을 잡아 촉촉함을 오래 유지합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음. 모든 피부에 무난합니다."},
    "hydrolyzed-hyaluronic-acid": {
        "category": "보습", "benefits": ["저분자 수분 공급", "속보습"],
        "description": "히알루론산을 잘게 쪼갠 저분자 형태. 분자가 작아 각질층 안쪽까지 수분을 전달해 속부터 촉촉하게 합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "retinol": {
        "category": "주름·안티에이징", "benefits": ["주름 개선", "탄력 증진", "피부결 정돈"],
        "description": "비타민A 유도체로 세포 턴오버를 촉진해 주름과 탄력을 개선하는 안티에이징 대표 성분. 효과가 강해 적응 기간이 필요합니다.",
        "skin_types": st({"건성": "caution", "민감성": "bad"}), "safety_grade": 6,
        "cautions": "초기 각질·붉어짐 가능. 저농도부터 주 2~3회 시작, 낮에는 자외선차단제 필수. 임산부 사용 금지."},
    "ascorbic-acid": {
        "category": "미백·톤개선", "benefits": ["미백", "항산화", "콜라겐 생성 촉진"],
        "description": "순수 비타민C. 멜라닌 생성을 억제해 기미·잡티를 옅게 하고 톤을 환하게 가꿉니다. 항산화·탄력에도 기여합니다.",
        "skin_types": st({"민감성": "caution"}), "safety_grade": 1,
        "cautions": "산성이 강해 민감성 피부는 따가움 가능. 갈변된 제품은 사용 중단."},
    "3-o-ethyl-ascorbic-acid": {
        "category": "미백·톤개선", "benefits": ["미백", "항산화", "안정성 우수"],
        "description": "비타민C 유도체 중 안정성이 뛰어난 형태. 순수 비타민C의 미백 효과를 유지하면서 쉽게 산화되지 않아 자극이 덜합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "magnesium-ascorbyl-phosphate": {
        "category": "미백·톤개선", "benefits": ["미백", "항산화", "저자극"],
        "description": "물에 안정적인 비타민C 유도체. 순수 비타민C보다 순해 민감성 피부도 부담 없이 미백·항산화 효과를 기대할 수 있습니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "tocopherol": {
        "category": "항산화", "benefits": ["항산화", "보습", "장벽 보호"],
        "description": "비타민E. 강력한 항산화 작용으로 활성산소로부터 피부를 보호하고, 다른 성분의 산화도 막아 제품을 안정시킵니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "ceramide-np": {
        "category": "장벽·보습", "benefits": ["피부 장벽 복구", "수분 손실 방지", "진정"],
        "description": "피부 장벽을 구성하는 핵심 지질. 세포 사이를 메워 수분 증발을 막고 외부 자극을 차단합니다. 손상된 장벽 회복에 우선 추천.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "panthenol": {
        "category": "진정·보습", "benefits": ["진정", "보습", "재생 보조"],
        "description": "프로비타민B5. 손상된 피부의 재생을 돕고 수분을 채워주는 순한 진정 성분입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "dexpanthenol": {
        "category": "진정·보습", "benefits": ["진정", "보습", "재생 보조"],
        "description": "판테놀의 활성형(프로비타민B5). 자극받은 피부를 빠르게 달래고 장벽 회복을 도와 더모 코스메틱 제품에 자주 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "adenosine": {
        "category": "주름·안티에이징", "benefits": ["주름 개선", "탄력 보조"],
        "description": "세포 에너지원에서 유래한 식약처 고시 주름개선 기능성 성분. 순하면서도 주름 완화 효과가 검증돼 안티에이징 제품에 널리 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "madecassoside": {
        "category": "진정·재생", "benefits": ["진정", "재생", "항염"],
        "description": "병풀(센텔라)의 핵심 활성 성분. 자극받은 피부를 빠르게 진정시키고 재생을 도와 시카 제품의 주역으로 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "madecassic-acid": {
        "category": "진정·재생", "benefits": ["진정", "항염", "재생 보조"],
        "description": "병풀에서 얻은 활성 성분으로, 붉어진 피부를 가라앉히고 피부 진정을 돕습니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "allantoin": {
        "category": "진정·재생", "benefits": ["진정", "각질 연화", "재생 보조"],
        "description": "각질을 부드럽게 하고 자극받은 피부를 달래는 순한 진정 성분. 민감성 피부 제품에 자주 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "arbutin": {
        "category": "미백·톤개선", "benefits": ["미백", "잡티 예방"],
        "description": "월귤잎 유래 미백 성분. 멜라닌 생성 효소를 억제해 기미·잡티를 예방하는 식약처 고시 미백 기능성 원료입니다.",
        "skin_types": st(), "safety_grade": 3, "cautions": "고온·빛에 분해될 수 있어 보관 주의."},
    "alpha-arbutin": {
        "category": "미백·톤개선", "benefits": ["미백", "잡티 예방", "흡수율 우수"],
        "description": "알부틴 중 미백 효율이 가장 높은 형태. 안정적이고 흡수가 잘 돼 톤 개선 효과가 뛰어납니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "특별한 주의사항 없음."},
    "tranexamic-acid": {
        "category": "미백·톤개선", "benefits": ["기미 완화", "색소침착 개선", "홍조 완화"],
        "description": "색소침착의 신호를 차단하는 신세대 미백 성분. 자극이 적어 민감성 피부의 기미·홍조 관리에도 적합합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "salicylic-acid": {
        "category": "각질·모공", "benefits": ["모공 속 각질 제거", "블랙헤드 완화", "여드름 예방"],
        "description": "지용성 각질 제거 성분(BHA). 모공 속 피지와 노폐물까지 녹여내 블랙헤드·여드름 관리의 핵심입니다.",
        "skin_types": st({"건성": "caution", "민감성": "caution"}), "safety_grade": 3,
        "cautions": "건성 피부는 과사용 시 당김 유발. 국내 화장품 배합 한도 0.5%."},
    "glycolic-acid": {
        "category": "각질·모공", "benefits": ["각질 제거", "피부결 개선", "톤 균일화"],
        "description": "사탕수수 유래 수용성 각질 제거 성분(AHA). 분자가 작아 묵은 각질을 정리해 피부결을 매끈하게 합니다.",
        "skin_types": st({"민감성": "bad", "여드름성": "caution"}), "safety_grade": 4,
        "cautions": "사용 후 자외선 민감도 증가 — 자외선차단제 필수."},
    "propolis-extract": {
        "category": "진정·영양", "benefits": ["항균", "진정", "영양·윤기 공급"],
        "description": "꿀벌이 만드는 천연 수지 추출물. 항균·항산화 성분이 풍부해 트러블 진정과 윤기 부여에 좋습니다.",
        "skin_types": st({"민감성": "caution"}), "safety_grade": 2,
        "cautions": "벌·꿀 알레르기가 있다면 패치 테스트 필수."},
    "camellia-sinensis-leaf-extract": {
        "category": "항산화", "benefits": ["항산화", "피지 산화 방지", "진정"],
        "description": "녹차잎 추출물. 카테킨(EGCG)이 풍부해 활성산소로부터 피부를 보호하고 피지 산화를 막아줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "houttuynia-cordata-extract": {
        "category": "진정·트러블", "benefits": ["진정", "항염", "트러블 완화"],
        "description": "약모밀(어성초) 추출물. 항염 작용이 뛰어나 예민하고 트러블 잦은 피부를 차분하게 진정시킵니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "centella-asiatica-leaf-extract": {
        "category": "진정·재생", "benefits": ["진정", "재생", "홍조 완화"],
        "description": "병풀 잎 추출물. 자극받은 피부를 빠르게 진정시키고 재생을 돕는 시카 케어의 대표 성분입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "squalane": {
        "category": "보습·오일", "benefits": ["보습", "유수분 밸런스", "피부 유연화"],
        "description": "피지와 유사한 구조의 가벼운 오일. 끈적임 없이 흡수돼 유분막을 만들어 수분 증발을 막습니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "bakuchiol": {
        "category": "주름·안티에이징", "benefits": ["주름 개선", "탄력 보조", "저자극"],
        "description": "식물 유래 '천연 레티놀 대안'. 레티놀과 비슷한 주름·탄력 개선 효과를 내면서 자극이 적어 민감성 피부도 쓸 수 있습니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "특별한 주의사항 없음."},
    "caffeine": {
        "category": "탄력·부기 케어", "benefits": ["부기 완화", "항산화", "혈행 보조"],
        "description": "혈행을 자극해 부기를 빼주는 성분. 특히 눈가 붓기·다크서클 케어 아이크림에 자주 쓰입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "zinc-oxide": {
        "category": "자외선차단", "benefits": ["UVA·UVB 차단", "저자극", "진정 보조"],
        "description": "자외선을 반사·산란시키는 무기(미네랄) 자외선차단 성분. 자극이 적어 민감성 피부 선크림에 주로 쓰입니다.",
        "skin_types": st(), "safety_grade": 2, "cautions": "백탁 현상이 있을 수 있음."},
    "glycerin": {
        "category": "보습", "benefits": ["수분 공급", "피부 유연화", "장벽 보조"],
        "description": "가장 오래되고 검증된 보습 성분. 수분을 끌어와 각질층에 채워주는 휴멕턴트의 표준입니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "ethylhexylglycerin": {
        "category": "보존 보조·보습", "benefits": ["보존 보조", "보습", "데오드란트 효과"],
        "description": "순한 보존 보조 성분. 페녹시에탄올 등과 함께 쓰여 적은 양으로 제품을 안전하게 지키고 가벼운 보습도 더합니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "특별한 주의사항 없음."},
    "soluble-collagen": {
        "category": "보습·탄력", "benefits": ["표면 보습", "피부 유연화", "일시적 탄력감"],
        "description": "가수분해하지 않은 천연 콜라겐. 피부 표면에 보습막을 형성해 촉촉함과 매끄러움을 줍니다.",
        "skin_types": st(), "safety_grade": 1, "cautions": "동물 유래 성분 — 비건 제품을 찾는다면 확인 필요."},
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
    drafts = sum(1 for i in data["ingredients"] if i.get("status") == "draft")
    pub = sum(1 for i in data["ingredients"] if i.get("status") == "published")
    not_found = [k for k in ENRICH if not any(i["id"] == k for i in data["ingredients"])]
    print(f"대표 성분 {filled}개 게시. 전체 게시 {pub} / 남은 draft {drafts}")
    if not_found:
        print("주의 — 데이터에 없는 id:", not_found)


if __name__ == "__main__":
    main()
