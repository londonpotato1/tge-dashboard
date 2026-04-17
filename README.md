# TGE & FDV Dashboard

10개 pre-TGE / 신규 런치 크립토 프로젝트의 밸류에이션 비교 대시보드. Polymarket FDV 확률 · 토크노믹스 · 백커 · 커뮤니티 반응을 한 페이지에서 비교할 수 있고, TGE dump short 매력도 랭킹 차트를 포함합니다.

데이터 기준: 2026-04-17 / Polymarket 스냅샷: CryptoDep 2026-04-15

## 주요 기능

- **10개 프로젝트 카드뷰**: Pharos, Variational, Fluent, USD.AI, Extended, Solstice, Ink, GRVT, Octra, Surf
- **정렬**: FDV / Polymarket 신뢰도 / 리스크 / Short 매력도
- **필터**: TGE 완료 / Pre-TGE
- **URL 쿼리로 필터 공유**: `?filter=pre-tge&sort=short` 같은 링크 공유 가능
- **다크모드 토글**: 시스템 설정 자동 감지 + 수동 전환
- **TGE short 매력도 차트**: 100점 만점 랭킹 + 티어 분석
- **JSON 데이터 분리**: `data/projects.json` 수정만으로 카드 내용 업데이트

## 로컬에서 실행

`file://` 프로토콜로 열면 fetch가 막히므로 로컬 서버 필요:

```bash
# Python 3
python3 -m http.server 8000

# Node.js
npx serve

# 그 후 브라우저에서 http://localhost:8000
```

## GitHub Pages 배포

### 1. 새 레포 만들기

GitHub에서 새 public 레포 생성 (예: `tge-dashboard`). 로컬에서:

```bash
git init
git add .
git commit -m "Initial commit: TGE & FDV Dashboard"
git branch -M main
git remote add origin https://github.com/londonpotato1/tge-dashboard.git
git push -u origin main
```

### 2. GitHub Pages 활성화

1. 레포 페이지 → **Settings** → 좌측 메뉴 **Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / `/ (root)` 선택 후 Save
4. 1-2분 후 `https://londonpotato1.github.io/tge-dashboard/` 에서 접속 가능

### 3. 커스텀 도메인 (선택)

Settings → Pages → **Custom domain**에 도메인 입력 후, DNS에 CNAME 레코드 추가:
```
CNAME  tge.your-domain.com  →  londonpotato1.github.io
```

## 데이터 업데이트 방법

`data/projects.json`에서 각 프로젝트 필드 수정 후 `git push`만 하면 GitHub Pages가 자동 재배포합니다.

주요 필드:
- `fdvPoly`: Polymarket 확률 문자열 (`">$100M (91%), $200M (58%)"` 형식 유지)
- `pmMode` / `pmMedian`: 정렬에 사용되므로 숫자 포함 필수
- `shortScore`: TGE short 매력도 0-100
- `risk`: `"낮음" | "중" | "고" | "매우 고"`
- `status`: `"launched" | "pre-tge"`
- `catColor` / `riskColor`: `purple | teal | blue | coral | pink | amber | green | gray | red`

## 파일 구조

```
tge-dashboard/
├── index.html          # 메인 페이지 (HTML + CSS + JS 통합)
├── data/
│   └── projects.json   # 프로젝트 데이터 (업데이트용)
├── README.md           # 이 파일
├── DEPLOY.md           # 상세 배포 가이드
└── .gitignore
```

## 기술 스택

- 바닐라 HTML/CSS/JS (프레임워크 없음)
- Chart.js 4.4.1 (jsdelivr CDN)
- GitHub Pages 호환 (빌드 스텝 없음)

## 주의사항

- 이 대시보드는 정보 제공 목적이며 투자 조언이 아닙니다
- Polymarket 확률은 시장 참여자 배팅이며 실제 FDV 보장이 아님
- TGE 일정은 프로젝트 측 공식 발표 기준으로 수시 업데이트 필요

## License

MIT
