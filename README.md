# 🌿 성분 사전 — 화장품 성분 안내 페이지 자동화

화장품 성분을 쉽게 설명하고 피부타입별 추천을 제공하는 웹페이지와,
신규 성분을 자동 수집해 페이지를 계속 생산하는 파이프라인입니다.

## 구조

```
ingredient-guide/
├── data/ingredients.json   # 성분 데이터 (단일 소스)
├── template.html           # 페이지 디자인 템플릿
├── generate_page.py        # JSON → index.html 생성기
├── crawler.py              # 신규 성분 자동 수집기
└── index.html              # 완성된 페이지 (브라우저로 열기)
```

## 동작 흐름

```
[crawler.py] 공식 DB에서 신규 성분 수집
      ↓ 기존 데이터와 비교, 새 성분만 draft로 추가
[ingredients.json] 데이터 취합
      ↓
[generate_page.py] published 성분만 골라 HTML 생성
      ↓
[index.html] 고객용 성분 안내 페이지
```

신규 성분은 `status: "draft"`로 들어와 **페이지에 노출되지 않습니다.**
설명·피부타입·안전등급을 채운 뒤 `"published"`로 바꾸면 게시됩니다.
(잘못된 정보가 고객에게 바로 나가는 것을 막는 검수 단계)

## 사용법

### 1. 페이지 생성
```bash
python generate_page.py
```
→ 다음 3가지를 한 번에 생성합니다:
- `index.html` — 검색·필터가 있는 전체 목록 (더블클릭으로 열기)
- `detail/{성분id}.html` — 성분별 SEO 상세 페이지 (게시 성분 1개당 1개)
- `sitemap.xml` — 검색엔진 색인용

배포 도메인이 정해지면 `--base-url`로 절대 URL을 넣어 sitemap·canonical을 완성합니다:
```bash
python generate_page.py --base-url https://ingredients.mybrand.com/
```
메인 페이지만 빠르게 갱신하려면 `--no-details`를 씁니다.

**SEO 상세 페이지에 포함되는 요소:** 고유 `<title>`·`description`, `canonical` 링크,
Open Graph 태그, JSON-LD 구조화 데이터(`DefinedTerm`), 같은 카테고리 성분 내부 링크,
빵부스러기(breadcrumb) 내비게이션. 메인 페이지의 각 성분 카드는 상세 페이지로 연결됩니다.

### 2. 신규 성분 수집

**인기 성분 위주로 수집 (권장)** — `--popular` 옵션은 히알루론산·나이아신아마이드·레티놀·세라마이드·펩타이드 등 수요 높은 30개 성분 키워드로만 검색해, 잘 안 쓰는 보조 성분이 무더기로 섞이는 것을 막아줍니다. 키워드 목록은 `crawler.py`의 `POPULAR_QUERIES`에서 수정할 수 있습니다.
```bash
pip install requests --break-system-packages
MFDS_API_KEY=발급받은키 python crawler.py --source mfds --popular
python crawler.py --source cosing --popular
```
키워드당 수집 개수는 `--per-query`로 조절합니다 (기본 10).

**특정 검색어로 수집** — 식약처는 한글 표준명, CosIng은 영문으로 검색합니다:
```bash
MFDS_API_KEY=발급받은키 python crawler.py --source mfds --query 하이알루로닉 --limit 20
python crawler.py --source cosing --query "peptide" --limit 20
```
※ 식약처 표준명은 외래어를 "하이-" 식으로 표기합니다 (히알루론산 → `하이알루로닉`).

**전체 순서대로 수집** — 인기도와 무관하게 등록순:
```bash
MFDS_API_KEY=발급받은키 python crawler.py --source mfds --limit 50
python crawler.py --source cosing --limit 50
```
※ 과거 안내했던 data.europa.eu CSV 데이터셋은 삭제되어 더 이상 사용할 수 없습니다.

### 3. 정기 자동 실행 (선택)
macOS/Linux cron — 매주 월요일 오전 9시:
```
0 9 * * 1 cd /경로/ingredient-guide && MFDS_API_KEY=키 python3 crawler.py --source mfds
```

## 데이터 스키마

| 필드 | 설명 |
|---|---|
| `korean_name` / `inci_name` | 한글명 / INCI 영문명 |
| `category` | 보습, 미백·톤개선, 진정·재생 등 |
| `description` | 고객용 쉬운 설명 |
| `skin_types` | 피부타입별 `good`(추천) / `caution`(주의) / `bad`(비추천) |
| `safety_grade` | 1~10, EWG Skin Deep 참고 (낮을수록 안전) |
| `status` | `published`(게시) / `draft`(검수 대기) |

## 확장 아이디어 (브랜드 로드맵 연계)

- 피부타입 진단 퀴즈 → 성분 추천 → 제품 추천으로 연결
- 성분별 상세 페이지 분리 생성 (SEO용, `--out` 옵션 활용)
- 식품·영양제 성분으로 동일 스키마 확장
- AI로 draft 성분의 설명 초안 자동 작성 후 검수

## 주의

안전등급·주의사항은 참고용입니다. 제품 출시 단계에서는 식약처 고시,
배합 한도 규정의 원자료를 반드시 직접 확인하세요.
