# Phase 1 진단 노트 (2026-05-15)

## 현재 상태

| 항목 | 값 |
|---|---|
| Repo | `londonpotato1/tge-dashboard` (public) |
| Commits | 4건 (마지막 2026-04-17 push) |
| 데이터 기준 | 2026-04-15 Polymarket / 2026-04-17 일반 |
| Pages URL | https://londonpotato1.github.io/tge-dashboard/ |
| 자동화 | 없음 (cron / fetch script 미존재) |
| Branch protection | 미설정 (404) |

## v5 plan §4 와 GAP

1. **Schema flat → nested 마이그레이션 필요**: `{static, live, lastVerified}` 구조 없음
2. **Polymarket event_slug 매니페스트 없음**: 10건 dry-run 에서 확정한 slug 박아두기
3. **Live writable paths 가드 부재**: fetch script 자체가 없음
4. **UI 상태 분기 부족**: 현재 2 state (`launched`/`pre-tge`) → 5 state 로 확장 필요
5. **CoinGecko / DefiLlama 연동 부재**: launched 토큰 가격/시총 라이브 없음
6. **Cron workflow 부재**: `.github/workflows/refresh-data.yml` 신규 작성
7. **Stat-card 하드코딩** (`index.html:348-360`): "Fluent, USD.AI, Octra" → derived 로 전환
8. **XSS 가드 부분적**: `innerHTML` 사용 (`render()` line 456). `esc()` / `safeUrl()` 헬퍼 추가 필요

## Phase 1-B 사전 결정

| 항목 | 결정 | 근거 |
|---|---|---|
| **Pharos 상태** | `launched` | CoinGecko API: id=`pharos-network`, symbol=PROS, rank=308 (등록 + 거래 가능) |
| **launched 4건** | Pharos / Fluent / USD.AI / Octra | Polymarket dry-run resolved + 2026-05-15 시점 TGE 완료 |
| **pre-tge 6건** | Variational / Extended / Solstice / Ink / GRVT / Surf | Polymarket dry-run active |

## krw-listing 실측 (Phase 1 게이트)

- 30분 cron 3일간 (144회 cron) 중 `data: live refresh` commit ≈ 10건
- **commit skip rate ≈ 93%** → idempotency guard 잘 작동중
- 동일 `_flatten_diff` 패턴 채용 확정

## Polymarket Manifest (dry-run 확정)

| Project | event_slug | 상태 |
|---|---|---|
| Pharos | `pharos-network-fdv-above-one-day-after-launch` | resolved |
| Variational | `variational-fdv-above-one-day-after-launch` | active |
| Fluent | `fluent-fdv-above-one-day-after-launch` | resolved |
| USD.AI | `usdai-fdv-above-one-day-after-launch` | resolved |
| Extended | `extended-fdv-above-one-day-after-launch` | active |
| Solstice | `solstice-fdv-above-one-day-after-launch` | active |
| Ink | `ink-fdv-above-one-day-after-launch` | active |
| GRVT | `grvt-fdv-above-one-day-after-launch` | active |
| Octra | `octra-fdv-above-one-day-after-launch` | resolved |
| Surf | `surf-fdv-above-one-day-after-launch` | active |

## 위험 점

- `index.html:456 innerHTML` 직접 출력 — XSS 가드 필수 (`esc()` / `safeUrl()`)
- `index.html:381` PROJECTS 정렬 로직이 `pmMedianNum()` (string regex 의존) — schema 변경 시 깨짐
- chart data 도 `PROJECTS` 직접 의존 (line 617)
