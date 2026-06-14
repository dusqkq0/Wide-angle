#!/usr/bin/env python3
"""SNS 공유용 OG 이미지 생성 (1200x630, 한글 Noto Sans CJK KR).
 - og-image.png : 사이트 기본 카드
 - og-result-{slug}.png : 피부타입별 결과 카드 5장 (공유 미리보기용)
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent
W, H = 1200, 630
NOTO = "/usr/share/fonts/opentype/noto/NotoSansCJK-{}.ttc"
def font(weight, size): return ImageFont.truetype(NOTO.format(weight), size, index=1)

ACCENT=(140,106,79); INK=(43,38,34); SUB=(138,127,118); GREEN=(58,155,110)

TYPES = [
    ("dry", "건성", "수분·유분이 부족해요. 보습·장벽 케어가 핵심"),
    ("oily", "지성", "피지가 많아요. 피지 조절 + 가벼운 보습"),
    ("sensitive", "민감성", "쉽게 예민해져요. 진정과 순한 성분 위주"),
    ("combination", "복합성", "부위별로 달라요. 나눠서 관리"),
    ("acne", "여드름성", "트러블이 잦아요. 모공·진정 케어"),
]


def gradient():
    img = Image.new("RGB", (W, H)); px = img.load()
    c1, c2 = (245, 236, 226), (227, 208, 187)
    for y in range(H):
        t = y/H
        row = (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))
        for x in range(W):
            px[x, y] = row
    return img


def center(d, text, y, fnt, fill):
    bb = d.textbbox((0, 0), text, font=fnt); w = bb[2]-bb[0]
    d.text(((W-w)//2, y), text, font=fnt, fill=fill)


def base_card():
    img = gradient(); d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 70, W-60, H-70], radius=36, fill=(255, 255, 255))
    center(d, "성분 사전", 140, font("Bold", 92), INK)
    center(d, "화장품 성분, 내 피부에 맞는지 1분이면 OK", 270, font("Regular", 38), ACCENT)
    center(d, "5,000+ 성분 · 안전등급 · 피부타입별 추천", 345, font("Regular", 34), SUB)
    center(d, "피부타입 진단   전성분 분석   성분 궁합 체크", 440, font("Bold", 33), GREEN)
    center(d, "식약처 · CosIng · EWG 공개 자료 기반", 520, font("Regular", 27), SUB)
    img.save(BASE/"og-image.png", "PNG")
    print("[OK] og-image.png")


def type_recs(data, kor):
    pool = [i for i in data["ingredients"]
            if i.get("status", "published") == "published"
            and i.get("skin_types", {}).get(kor) == "good"
            and "주의 성분" not in i.get("category", "")]
    pool.sort(key=lambda i: i.get("safety_grade", 5))
    return [i["korean_name"] for i in pool[:3]]


def result_card(slug, kor, lead, recs):
    img = gradient(); d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 60, W-60, H-60], radius=36, fill=(255, 255, 255))
    center(d, "성분 사전 · 피부 진단", 120, font("Bold", 36), ACCENT)
    center(d, "내 피부타입은", 210, font("Regular", 36), SUB)
    center(d, f"{kor} 피부", 270, font("Bold", 94), INK)
    center(d, lead, 410, font("Regular", 30), SUB)
    if recs:
        center(d, "추천 성분  " + "  ".join("#"+r for r in recs), 490, font("Bold", 32), GREEN)
    center(d, "나도 1분 진단하기 →", 555, font("Regular", 28), ACCENT)
    img.save(BASE/f"og-result-{slug}.png", "PNG")
    print(f"[OK] og-result-{slug}.png ({kor})")


if __name__ == "__main__":
    base_card()
    data = json.loads((BASE/"data/ingredients.json").read_text(encoding="utf-8"))
    for slug, kor, lead in TYPES:
        result_card(slug, kor, lead, type_recs(data, kor))
