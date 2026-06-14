#!/usr/bin/env python3
"""성분 데이터(JSON) → 성분 사전 HTML 생성기.

- 메인 페이지(index.html): 검색·필터가 있는 전체 목록
- 성분별 상세 페이지(detail/{id}.html): SEO 최적화된 개별 페이지
- sitemap.xml: 검색엔진 색인용

사용법:
    python generate_page.py                      # index + 상세 + sitemap 전부 생성
    python generate_page.py --out site/          # 출력 폴더 지정
    python generate_page.py --no-details         # 메인 페이지만
    python generate_page.py --base-url https://example.com/  # 절대 URL(sitemap·canonical용)
"""
import argparse
import html as html_lib
import json
import re
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent

SKIN_LABEL = {"good": "추천", "caution": "주의", "bad": "비추천"}


def esc(s) -> str:
    return html_lib.escape(str(s), quote=True)


def grade_color(g: int) -> str:
    return "#3a9b6e" if g <= 2 else "#c98a1b" if g <= 6 else "#c4534f"


def grade_text(g: int) -> str:
    return "낮은 위험" if g <= 2 else "보통" if g <= 6 else "높은 위험"


def published(data: dict) -> list:
    return [i for i in data["ingredients"] if i.get("status", "published") == "published"]


def load_site(base_dir: Path) -> dict:
    """data/site.json 로드 (전역 설정)."""
    p = base_dir / "data/site.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def site_meta_html(site: dict) -> str:
    """검색엔진 소유확인 + OG/트위터 공유 메타태그 HTML 생성."""
    tags = []
    if site.get("google_site_verification"):
        tags.append(f'<meta name="google-site-verification" content="{esc(site["google_site_verification"])}" />')
    if site.get("naver_site_verification"):
        tags.append(f'<meta name="naver-site-verification" content="{esc(site["naver_site_verification"])}" />')
    base = site.get("base_url", "").rstrip("/")
    if base:
        og = f"{base}/og-image.png"
        title = "성분 사전 — 내 피부에 맞는 화장품 성분 찾기"
        desc = "화장품 성분을 피부타입별로 쉽게 확인하고, 전성분 분석·성분 궁합까지. 5,000+ 성분 데이터."
        tags += [
            '<meta property="og:type" content="website" />',
            f'<meta property="og:title" content="{title}" />',
            f'<meta property="og:description" content="{desc}" />',
            f'<meta property="og:image" content="{og}" />',
            '<meta property="og:image:width" content="1200" />',
            '<meta property="og:image:height" content="630" />',
            f'<meta property="og:url" content="{base}/" />',
            '<meta name="twitter:card" content="summary_large_image" />',
            f'<meta name="twitter:title" content="{title}" />',
            f'<meta name="twitter:description" content="{desc}" />',
            f'<meta name="twitter:image" content="{og}" />',
        ]
    return "\n".join(tags)


def load_products(base_dir: Path) -> dict:
    """data/products.json 로드. 없으면 빈 구조 반환. status='active'인 제품만 사용."""
    p = base_dir / "data/products.json"
    if not p.exists():
        return {"affiliate_notice": "", "products": []}
    raw = json.loads(p.read_text(encoding="utf-8"))
    raw["products"] = [x for x in raw.get("products", []) if x.get("status") == "active"]
    return raw


def product_cards_html(products: list) -> str:
    """제품 카드 묶음 HTML (상세 페이지용)."""
    cards = []
    for p in products:
        img = (f'<img src="{esc(p["image"])}" alt="{esc(p["name"])}" loading="lazy">'
               if p.get("image") else "")
        price = f'<span class="pprice">{esc(p["price"])}</span>' if p.get("price") else ""
        note = f'<div class="pnote">{esc(p["note"])}</div>' if p.get("note") else ""
        src = esc(p.get("source", "")) or "제휴처"
        badge = f'<span class="psrc">{esc(p["source"])}</span>' if p.get("source") else ""
        cards.append(
            f'<a class="pcard" href="{esc(p["url"])}" target="_blank" rel="nofollow sponsored noopener">'
            f'{img}<div class="pbody">{badge}<div class="pname">{esc(p["name"])}</div>{note}'
            f'<div class="pbuy">{price}<span class="pbtn">{src}에서 보기 →</span></div></div></a>'
        )
    return "".join(cards)


def _inject(data_path: Path, template_path: Path, out_path: Path) -> int:
    """템플릿의 /*__DATA__*/·<!--__SITE_META__--> 자리에 데이터·설정을 주입해 저장."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    data["ingredients"] = published(data)
    data["meta"]["updated"] = date.today().isoformat()
    site = load_site(out_path.parent)

    template = template_path.read_text(encoding="utf-8")
    html = template.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    html = html.replace("<!--__SITE_META__-->", site_meta_html(site))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return len(data["ingredients"])


def generate(data_path: Path, template_path: Path, out_path: Path) -> int:
    """메인 페이지 생성."""
    return _inject(data_path, template_path, out_path)


def generate_with_products(data_path: Path, template_path: Path, out_path: Path) -> int:
    """성분 + 제휴 제품 + 사이트 설정을 모두 주입 (퀴즈·분석기 공용)."""
    return generate_quiz(data_path, template_path, out_path)


def generate_quiz(data_path: Path, template_path: Path, out_path: Path) -> int:
    """성분 + 제휴 제품 + 사이트 데이터 주입 (퀴즈·분석기 공용)."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    data["ingredients"] = published(data)
    data["meta"]["updated"] = date.today().isoformat()
    products = load_products(out_path.parent)
    site = load_site(out_path.parent)
    combos_path = out_path.parent / "data/combos.json"
    combos = json.loads(combos_path.read_text(encoding="utf-8")) if combos_path.exists() else {"rules": []}
    avoid_path = out_path.parent / "data/avoid_rules.json"
    avoid = json.loads(avoid_path.read_text(encoding="utf-8")) if avoid_path.exists() else {"situations": []}

    template = template_path.read_text(encoding="utf-8")
    html = template.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    html = html.replace("/*__PRODUCTS__*/", json.dumps(products, ensure_ascii=False))
    html = html.replace("/*__COMBOS__*/", json.dumps(combos, ensure_ascii=False))
    html = html.replace("/*__AVOID__*/", json.dumps(avoid, ensure_ascii=False))
    html = html.replace("/*__KAKAO__*/", site.get("kakao_channel_url", ""))
    html = html.replace("/*__SITEURL__*/", site.get("base_url", ""))
    html = html.replace("/*__ALLOWED__*/", json.dumps(site.get("widget_allowed_domains", []), ensure_ascii=False))
    html = html.replace("<!--__SITE_META__-->", site_meta_html(site))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return len(data["ingredients"])


DETAIL_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Apple SD Gothic Neo','Pretendard','Noto Sans KR',sans-serif;background:#faf7f4;color:#2b2622;line-height:1.7}
.wrap{max-width:760px;margin:0 auto;padding:24px}
.crumb{font-size:13px;color:#8a7f76;margin:8px 0 20px}
.crumb a{color:#b08968;text-decoration:none}
.card{background:#fff;border:1px solid #eee5dd;border-radius:18px;padding:32px;margin-bottom:20px}
.cat{display:inline-block;font-size:12px;background:#f3ece5;color:#8c6a4f;padding:5px 12px;border-radius:999px;margin-bottom:14px}
h1{font-size:28px;font-weight:800;letter-spacing:-0.5px}
.inci{font-size:14px;color:#8a7f76;margin-top:4px}
.grade{display:flex;align-items:center;gap:10px;margin:20px 0;font-size:14px}
.gbadge{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:15px}
.desc{font-size:16px;color:#4d453e;margin:18px 0}
h2{font-size:16px;font-weight:700;margin:24px 0 10px;color:#6e4f3a}
.tags{display:flex;flex-wrap:wrap;gap:8px}
.tag{font-size:13px;background:#f6f1ec;color:#6e635a;padding:5px 11px;border-radius:7px}
table{width:100%;border-collapse:collapse;margin-top:6px}
td{padding:9px 12px;border-bottom:1px solid #f0e8e0;font-size:14px}
td:first-child{color:#6e635a;width:120px}
.pill{font-size:13px;padding:3px 10px;border-radius:6px;font-weight:600}
.good{background:#e7f5ee;color:#3a9b6e}.caution{background:#fdf3e0;color:#c98a1b}.bad{background:#fbe9e8;color:#c4534f}
.warn{font-size:14px;color:#9c6b3f;background:#fdf6ec;border-left:3px solid #c98a1b;padding:12px 14px;border-radius:0 8px 8px 0;margin-top:8px}
.related{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.related a{font-size:13px;background:#fff;border:1px solid #eee5dd;border-radius:999px;padding:7px 13px;color:#8c6a4f;text-decoration:none}
.related a:hover{background:#f3ece5}
.back{display:inline-block;margin-top:8px;color:#b08968;text-decoration:none;font-size:14px}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.pcard{display:flex;flex-direction:column;border:1px solid #eee5dd;border-radius:13px;overflow:hidden;text-decoration:none;color:inherit;background:#fff;transition:.15s}
.pcard:hover{border-color:#b08968;box-shadow:0 3px 12px rgba(176,137,104,.15)}
.pcard img{width:100%;height:140px;object-fit:cover;background:#f3ece5}
.pbody{padding:13px;display:flex;flex-direction:column;gap:6px;flex:1}
.psrc{align-self:flex-start;font-size:10.5px;font-weight:700;color:#3a9b6e;background:#e7f5ee;padding:2px 8px;border-radius:999px}
.pname{font-size:14px;font-weight:700;line-height:1.4}
.pnote{font-size:12px;color:#8a7f76;flex:1}
.pbuy{display:flex;align-items:center;justify-content:space-between;margin-top:4px}
.pprice{font-size:13px;font-weight:700;color:#8c6a4f}
.pbtn{font-size:12px;color:#b08968;font-weight:600}
.affiliate-notice{font-size:11.5px;color:#a4937f;background:#f6f1ec;border-radius:8px;padding:9px 12px;margin-top:10px;line-height:1.5}
footer{text-align:center;padding:30px 16px;font-size:12px;color:#8a7f76}
"""


def detail_html(ing: dict, related: list, base_url: str, products_data: dict = None) -> str:
    g = ing.get("safety_grade", 5)
    products_data = products_data or {"products": [], "affiliate_notice": ""}
    matched = [p for p in products_data["products"] if ing["id"] in p.get("ingredients", [])]
    products_block = ""
    if matched:
        notice = products_data.get("affiliate_notice", "")
        products_block = (
            f'<div class="card"><h2 style="margin-top:0">🛒 이 성분이 든 추천 제품</h2>'
            f'<div class="products">{product_cards_html(matched)}</div>'
            + (f'<div class="affiliate-notice">{esc(notice)}</div>' if notice else "")
            + "</div>"
        )
    title = f"{ing['korean_name']} ({ing['inci_name']}) — 효능·피부타입별 추천 | 성분 사전"
    meta_desc = re.sub(r"\s+", " ", ing.get("description", ""))[:155]
    canonical = f"{base_url}detail/{ing['id']}.html" if base_url else f"{ing['id']}.html"

    benefits = "".join(f'<span class="tag">#{esc(b)}</span>' for b in ing.get("benefits", []))
    rows = "".join(
        f'<tr><td>{esc(k)}</td><td><span class="pill {v}">{SKIN_LABEL.get(v, v)}</span></td></tr>'
        for k, v in ing.get("skin_types", {}).items()
    )
    rel = "".join(
        f'<a href="{esc(r["id"])}.html">{esc(r["korean_name"])}</a>' for r in related
    )
    cautions = (
        f'<h2>⚠️ 사용 시 주의</h2><div class="warn">{esc(ing["cautions"])}</div>'
        if ing.get("cautions") else ""
    )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": ing["korean_name"],
        "alternateName": ing["inci_name"],
        "description": meta_desc,
        "inDefinedTermSet": "화장품 성분 사전",
    }

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta_desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(ing['korean_name'])} 성분 정보 | 성분 사전">
<meta property="og:description" content="{esc(meta_desc)}">
<meta property="og:url" content="{esc(canonical)}">
{(f'<meta property="og:image" content="{esc(base_url)}og-image.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{esc(base_url)}og-image.png">' if base_url else '')}
<meta name="robots" content="index,follow">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{DETAIL_CSS}</style>
</head>
<body>
<div class="wrap">
  <nav class="crumb"><a href="../index.html">성분 사전</a> › {esc(ing['category'])} › {esc(ing['korean_name'])}</nav>
  <article class="card">
    <span class="cat">{esc(ing['category'])}</span>
    <h1>{esc(ing['korean_name'])}</h1>
    <div class="inci">{esc(ing['inci_name'])}{(' · CAS ' + esc(ing['cas_no'])) if ing.get('cas_no') else ''}</div>
    <div class="grade"><span class="gbadge" style="background:{grade_color(g)}">{g}</span>
      <span>안전등급 {g} — {grade_text(g)} <small style="color:#a4937f">(EWG Skin Deep 참고)</small></span></div>
    <p class="desc">{esc(ing['description'])}</p>
    <h2>주요 효능</h2>
    <div class="tags">{benefits or '<span class="tag">정보 준비 중</span>'}</div>
    <h2>피부타입별 적합도</h2>
    <table>{rows}</table>
    {cautions}
  </article>
  {products_block}
  {f'<div class="card"><h2 style="margin-top:0">같은 카테고리 성분</h2><div class="related">{rel}</div></div>' if rel else ''}
  <a class="back" href="../index.html">← 전체 성분 목록으로</a>
</div>
<footer>데이터 출처: 식품의약품안전처 화장품 원료성분정보 · 대한화장품협회 성분사전 · EU CosIng · EWG Skin Deep 등 공개 자료 종합.<br>안전등급·효능은 참고용이며 의학적 판단의 근거가 아닙니다. 피부 고민이 지속되면 피부과 전문의와 상담하세요.</footer>
</body>
</html>"""


SKIN_TYPES = [
    ("dry", "건성", "수분과 유분이 부족해 당김·각질이 생기기 쉬운 타입이에요. 보습과 장벽 케어가 핵심입니다."),
    ("oily", "지성", "피지 분비가 많아 번들거림·모공이 고민이기 쉬운 타입이에요. 피지 조절과 가벼운 보습이 포인트."),
    ("sensitive", "민감성", "외부 자극에 쉽게 붉어지고 따가운 타입이에요. 진정·장벽 케어와 자극 요소 피하기가 중요합니다."),
    ("combination", "복합성", "T존은 번들거리고 볼은 건조한 타입이에요. 부위별로 나눠 관리하는 게 핵심입니다."),
    ("acne", "여드름성", "트러블이 잦은 타입이에요. 모공·피지 관리와 진정을 함께 챙기는 게 좋아요."),
]


def generate_result_pages(data_path: Path, out_dir: Path, base_url: str) -> int:
    """피부타입별 정적 결과 페이지 — SNS 공유 시 타입별 OG 미리보기가 뜨도록."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    items = published(data)
    rdir = out_dir / "result"
    rdir.mkdir(parents=True, exist_ok=True)
    for slug, kor, lead in SKIN_TYPES:
        recs = sorted(
            [i for i in items if i["skin_types"].get(kor) == "good" and "주의 성분" not in i["category"]],
            key=lambda i: i.get("safety_grade", 5))[:6]
        og = f"{base_url}og-result-{slug}.png" if base_url else f"../og-result-{slug}.png"
        cards = "".join(
            f'<a class="rc" href="../detail/{esc(i["id"])}.html">'
            f'<span class="rcg" style="background:{grade_color(i.get("safety_grade",5))}">{i.get("safety_grade","")}</span>'
            f'<span><b>{esc(i["korean_name"])}</b><br><small>{esc(i["category"])}</small></span></a>'
            for i in recs)
        title = f"나는 {kor} 피부 — 성분 사전 진단 결과"
        html = f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{kor} 피부에 맞는 화장품 성분을 확인하세요. 1분 무료 진단.">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{esc(lead)}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og}">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Apple SD Gothic Neo','Pretendard','Noto Sans KR',sans-serif;background:#faf7f4;color:#2b2622;line-height:1.7}}
header{{background:linear-gradient(150deg,#f5ece2,#e9d9c8);padding:46px 22px 36px;text-align:center}}
header .s{{font-size:14px;color:#8a7f76}} header h1{{font-size:30px;font-weight:800;margin-top:6px}}
header p{{color:#7a6a58;margin-top:10px;font-size:15px;max-width:520px;margin-left:auto;margin-right:auto}}
.wrap{{max-width:720px;margin:0 auto;padding:26px 20px}}
h2{{font-size:17px;color:#6e4f3a;margin-bottom:12px}}
.rc{{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #eee5dd;border-radius:13px;padding:13px 15px;margin-bottom:9px;text-decoration:none;color:inherit}}
.rc:hover{{border-color:#b08968}} .rc .rcg{{width:30px;height:30px;border-radius:8px;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px}}
.rc small{{color:#8a7f76}}
.cta{{display:block;text-align:center;margin:26px 0 10px;padding:16px;border-radius:14px;background:#b08968;color:#fff;text-decoration:none;font-size:17px;font-weight:700;box-shadow:0 4px 14px rgba(176,137,104,.35)}}
.nav{{text-align:center;margin-top:14px}} .nav a{{color:#b08968;text-decoration:none;font-size:14px;margin:0 8px}}
footer{{text-align:center;padding:30px 16px;font-size:12px;color:#8a7f76}}
</style></head>
<body>
<header>
  <div class="s">성분 사전 · 피부 진단 결과</div>
  <h1>🌿 {kor} 피부</h1>
  <p>{esc(lead)}</p>
</header>
<div class="wrap">
  <h2>✅ {kor} 피부에 추천하는 성분</h2>
  {cards}
  <a class="cta" href="../quiz.html">🧫 나도 1분 진단하고 내 피부타입 알아보기 →</a>
  <div class="nav"><a href="../index.html">성분 사전</a> · <a href="../analyzer.html">전성분 분석</a></div>
</div>
<footer>본 진단은 일반적인 참고용이며 의학적 진단이 아닙니다.</footer>
</body></html>"""
        (rdir / f"{slug}.html").write_text(html, encoding="utf-8")
    return len(SKIN_TYPES)


def generate_details(data_path: Path, out_dir: Path, base_url: str) -> int:
    """성분별 상세 페이지 + sitemap 생성."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    items = published(data)
    products_data = load_products(out_dir)
    detail_dir = out_dir / "detail"
    detail_dir.mkdir(parents=True, exist_ok=True)

    by_cat: dict[str, list] = {}
    for i in items:
        by_cat.setdefault(i["category"], []).append(i)

    for ing in items:
        related = [r for r in by_cat.get(ing["category"], []) if r["id"] != ing["id"]][:6]
        (detail_dir / f"{ing['id']}.html").write_text(
            detail_html(ing, related, base_url, products_data), encoding="utf-8"
        )

    # sitemap.xml
    today = date.today().isoformat()
    urls = [f"{base_url}index.html", f"{base_url}quiz.html", f"{base_url}analyzer.html",
            f"{base_url}combos.html", f"{base_url}avoid.html"] \
        + [f"{base_url}result/{s}.html" for s, _, _ in SKIN_TYPES] \
        + [f"{base_url}detail/{i['id']}.html" for i in items]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{esc(u)}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    (out_dir / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=BASE / "data/ingredients.json", type=Path)
    ap.add_argument("--template", default=BASE / "template.html", type=Path)
    ap.add_argument("--out", default=BASE / "index.html", type=Path)
    ap.add_argument("--quiz-template", default=BASE / "quiz_template.html", type=Path)
    ap.add_argument("--analyzer-template", default=BASE / "analyzer_template.html", type=Path)
    ap.add_argument("--no-quiz", action="store_true", help="진단 퀴즈 페이지 생성 생략")
    ap.add_argument("--base-url", default="",
                    help="배포 도메인 (예: https://ingredients.mybrand.com/). sitemap·canonical에 사용")
    ap.add_argument("--no-details", action="store_true", help="상세 페이지·sitemap 생략")
    args = ap.parse_args()

    base_url = args.base_url or load_site(args.out.parent).get("base_url", "")
    if base_url and not base_url.endswith("/"):
        base_url += "/"

    n = generate(args.data, args.template, args.out)
    print(f"[OK] {args.out} 생성 — 성분 {n}개 게시")

    if not args.no_quiz and args.quiz_template.exists():
        quiz_out = args.out.parent / "quiz.html"
        generate_quiz(args.data, args.quiz_template, quiz_out)
        print(f"[OK] {quiz_out} 진단 퀴즈 페이지 생성")

    if args.analyzer_template.exists():
        an_out = args.out.parent / "analyzer.html"
        generate_with_products(args.data, args.analyzer_template, an_out)
        print(f"[OK] {an_out} 전성분 분석기 생성")

    combos_tpl = args.out.parent / "combos_template.html"
    if combos_tpl.exists():
        combos_out = args.out.parent / "combos.html"
        generate_with_products(args.data, combos_tpl, combos_out)
        print(f"[OK] {combos_out} 성분 궁합·충돌 체크 생성")

    embed_tpl = args.out.parent / "embed_template.html"
    if embed_tpl.exists():
        embed_out = args.out.parent / "embed.html"
        generate_with_products(args.data, embed_tpl, embed_out)
        print(f"[OK] {embed_out} B2B 검색 위젯 생성")

    embed_an_tpl = args.out.parent / "embed_analyzer_template.html"
    if embed_an_tpl.exists():
        embed_an_out = args.out.parent / "embed-analyzer.html"
        generate_with_products(args.data, embed_an_tpl, embed_an_out)
        print(f"[OK] {embed_an_out} B2B 분석 위젯 생성")

    avoid_tpl = args.out.parent / "avoid_template.html"
    if avoid_tpl.exists():
        avoid_out = args.out.parent / "avoid.html"
        generate_with_products(args.data, avoid_tpl, avoid_out)
        print(f"[OK] {avoid_out} 상황별 회피 성분 필터 생성")

    if not args.no_details:
        out_dir = args.out.parent
        r = generate_result_pages(args.data, out_dir, base_url)
        print(f"[OK] result/ 피부타입별 결과 페이지 {r}개 생성 (공유 OG)")
        d = generate_details(args.data, out_dir, base_url)
        print(f"[OK] detail/ 상세 페이지 {d}개 + sitemap.xml 생성"
              + (f" (base-url: {base_url})" if base_url else " (상대경로)"))
