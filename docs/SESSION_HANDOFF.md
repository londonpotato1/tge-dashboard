# tge-dashboard 세션 핸드오프 (2026-05-15 02:42 KST)

> 재부팅 후 다음 세션 재개용. 이 파일 + v5 plan + projects.json 만 읽으면 완전 복원 가능.

## 한 줄 요약

Phase 1~3-B 완료, Phase 3-C (index.html UI 5-state) 부터 재개. 라이브 fetch 동작 검증됨.

## 완료 (Phase 1 ~ 3-B)

| Phase | 산출물 | 상태 |
|---|---|---|
| **0. Preflight** | branch protection 없음 / gh auth ✅ / COINGECKO_API_KEY 미등록 (anonymous 사용) / krw-listing skip 93% / Pharos launched 확정 | ✅ |
| **1. Clone + Diagnose** | `~/Projects/london_projects/tge-dashboard/` clone + `docs/NOTES.md` | ✅ |
| **2. Researcher** | `docs/research-2026-05-15.md` + `*-raw.jsonl` (200s) | ✅ |
| **3-A. Schema migration** | `data/projects.json` flat → nested ({static, polymarket, live, lastVerified}) + 10 manifest event_slug + 5 launched live.manifest | ✅ |
| **3-B. fetch_live_data.py** | `scripts/fetch_live_data.py` (170 line, 9 함수). Polymarket + CoinGecko + LIVE_WRITABLE_PATHS guard + idempotency (timestamp 외 변경 없으면 skip) | ✅ |

## 펜딩 (Phase 3-C ~ 6)

### Phase 3-C: index.html UI 5-state (다음 시작점)

`index.html` 22KB 수정. v5 plan §7 Phase 3-C 참조 (`/tmp/tge-dashboard-plan-v5.md`).

체크리스트:
- [ ] `esc()` / `safeUrl()` XSS 가드 헬퍼 (krw-listing 패턴 차용)
- [ ] `uiState(p)` 5-state 분기 함수 (`launched_priced` / `launched_no_price` / `pre_tge_market_active` / `pre_tge_resolved_only` / `pre_tge_no_market`)
- [ ] `render()` 분기 → uiState 별 카드 레이아웃
- [ ] last-refresh 뱃지 (`meta.live.batch_ts` 표시, **stale 임계 90분** — cron 60 + Pages lag 30)
- [ ] `partial_failure` ⚠ 뱃지
- [ ] PM outcome 미니바 (`p.polymarket.live.markets[].yes_price` 사용)
- [ ] stat-card 하드코딩 → derived 전환 (line 348-360: `id="stat-launched"`, `id="stat-launched-list"`)
- [ ] `</` → `<\/` script breakout 가드

새 필드 참조:
- `meta.live.batch_ts`, `meta.live.partial_failure`
- `p.polymarket.live.event_status` ('active' / 'partial' / 'resolved')
- `p.polymarket.live.markets[]` (각: threshold_label, threshold_usd, yes_price, last_traded, closed)
- `p.polymarket.live.resolution_summary` (resolved 시)
- `p.live.current_price_usd`, `current_fdv_usd`, `volume_24h_usd`
- `p.live.error` (null/string)

기존 정렬·필터 로직 (`pmMedianNum`, `getConfidence`) 도 새 schema 활용해 derived 로 교체 권장 (단 카파시: 1줄로 가능하면 1줄).

### Phase 4: GitHub Actions workflow

- `.github/workflows/refresh-data.yml` 작성 (1h cron, krw-listing 패턴 차용)
  - reference: `~/Desktop/krw-listing-dashboard/.github/workflows/refresh-data.yml`
- workflow inline `-c` block 은 sanity-only (manifest 보존, batch_ts 존재) — 진짜 guard 는 fetch script 내부 (Slop-3 명시)
- 수동 commit step: `git add data/projects.json && (git diff --cached --quiet && exit 0 || git commit -m ...)`
- `gh api -X PUT /repos/.../branches/main/protection` 으로 cron-friendly 보호 추가

### Phase 5: 검증

- `reviewer` subagent 1회 (LIVE_WRITABLE_PATHS, 5-state UI, XSS 가드, 카파시 슬롭 명시 판정)
- `codex-rescue` 메타 검토 1회 (reviewer 누락 영역, threshold regex edge, resolved 분기 robustness)
- `git secrets` / `innerHTML` grep

### Phase 6: 배포 + 24h 모니터링

- 분리 commit 4건: (a) schema (b) script + workflow (c) UI (d) content
- `git push` → Pages 60초 대기 → `curl -I` 200 확인
- Actions `workflow_dispatch` 수동 fire → 첫 라이브 commit 확인
- 24h: commit 빈도, skip rate, API 429 발생 여부

## 라이브 fetch 첫 결과 (2026-05-14 17:42 UTC)

| 토큰 | CoinGecko price | FDV | Polymarket resolution | 정확도 |
|---|---|---|---|---|
| Pharos | $0.74 | $736M | $800M Yes | ✅ ±9% |
| Fluent | $0.12 | $119M | $100M Yes | ✅ |
| USD.AI | $1.00 | $272M | $1B Yes | ⚠ Polymarket oracle 측 정산 부정확 (우리 코드는 yes_price≥0.99 정확) |
| Solstice | null | null | active | UI 5-state `launched_no_price` 분기 사용 |
| Octra | $0.056 | $35M | all No | ✅ |

## 알려진 이슈 / 보류

| 항목 | 결정 | 추적 |
|---|---|---|
| USD.AI ticker CHIP→USDAI | 보류 | Phase 5 검증 시 재확인 |
| USD.AI Polymarket "$1B Yes" vs 실제 $272M | 표시만, 노트 추가 | Phase 3-C UI 노트로 |
| Surf launched (PulseChain $76K meme) | 거부 (pre-tge 유지) | — |
| 모든 contract 주소 null | hook false-positive 차단 → CoinGecko ID 만으로 작동, 영향 없음 | future PR |
| Variational/Extended/Ink/GRVT 시기 미세 변경 | 보류 | — |

## 진입 명령 (다음 세션 첫 실행)

```bash
# 1. 작업 디렉토리 확인
cd ~/Projects/london_projects/tge-dashboard
ls -la
git status

# 2. fetch script 정상 동작 재확인 (선택)
python3 scripts/fetch_live_data.py

# 3. 핸드오프 + 플랜 다시 로드
cat docs/SESSION_HANDOFF.md
cat /tmp/tge-dashboard-plan-v5.md | head -250

# 4. index.html 현재 상태 읽기
wc -l index.html  # 691 lines 예상
# 핵심 함수 위치: render() line 452, pmMedianNum() 435, fetch() 668
```

## 산출물 위치

- 계획서: `/tmp/tge-dashboard-plan-v5.md` (재부팅 시 사라질 수 있음 — 영구화 필요시 `~/Projects/london_projects/tge-dashboard/docs/plan-v5.md` 로 복사)
- 진단: `docs/NOTES.md`
- 리서치: `docs/research-2026-05-15.md` (+`-raw.jsonl`)
- 코드: `scripts/fetch_live_data.py`
- 데이터: `data/projects.json` (라이브 1회 fetch 완료)
- 미수정: `index.html` (현재 원본 그대로)

## ⚠ 재부팅 전 백업 권장

`/tmp/tge-dashboard-plan-v5.md` 는 `/tmp` 라 재부팅 시 삭제 가능:

```bash
cp /tmp/tge-dashboard-plan-v5.md ~/Projects/london_projects/tge-dashboard/docs/plan-v5.md
```

(아직 안 함 — 사용자 판단)
