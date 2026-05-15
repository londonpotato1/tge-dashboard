# TGE Dashboard — Update & Live-Refresh 계획 v4 (FINAL)

> v1: `/tmp/tge-dashboard-plan.md` (Codex 1차: BLOCK 2 / FLAG 5)
> v2: `/tmp/tge-dashboard-plan-v2.md` (Codex 2차: BLOCK 4 / FLAG 7)
> v3: `/tmp/tge-dashboard-plan-v3.md` (Codex 3차 self-consistency: CONDITIONAL GO + micro-patch 4)
> **v4: reviewer 4차 검토 반영 (BLOCK 2 + FLAG 8 + Slop 4 모두 패치)**
> dry-run: `/tmp/polymarket-dryrun.md` (75/75 markets, 10/10 negRisk=False)
> 사용자 결정: 갱신 1시간 / branch protection 사용자 직접 확인

---

## 0-a. v3 → v4 변경사항 (reviewer BLOCK 2 + FLAG 8 + Slop 4 반영)

| reviewer 지적 | v4 대응 |
|---|---|
| BLOCK-1 writable path guard 이름만 있고 강제 없음 | ✅ §4.2 `validate_writable_paths()` 실제 구현 명세화 — before/after JSON diff + `LIVE_WRITABLE_PATHS` set 비교. workflow inline `-c` 는 "sanity-only" 주석 명시 |
| BLOCK-2 Pharos 상태 결정 유예 | ✅ Phase 1 산출물 명시 — preflight 1번째 항목 |
| FLAG-1 Phase 3 "병렬" 실행 주체 불명 | ✅ "3-A → 3-B → 3-C 순차 단일 처리" 로 확정 |
| FLAG-2 researcher literal prompt | ✅ Phase 2 에 prompt block 삽입 |
| FLAG-3 stale 60분 임계값 | ✅ **90분** (cron 60 + Pages lag 30) 로 변경 |
| FLAG-4 Polymarket shape assertion | ✅ `fetch_polymarket()` 응답 첫 처리에 shape assertion 명세 |
| FLAG-5 bad slug 영구 404 silent fail | ✅ 연속 3회 fail 시 `sys.exit(1)` 명시 |
| FLAG-6 §9 진입 조건 보완 | ✅ COINGECKO ping / Actions 실패 디버그 / krw-listing skip 실측 추가 |
| FLAG-7 부분 실패 batch_ts 일관성 | ✅ `meta.live.partial_failure` 플래그 + 소스별 `pulled_at` 분리 |
| FLAG-8 krw-listing skip 비율 실측 | ✅ Phase 1 preflight 측정 명령 명시 |
| Slop-1 projects.v1.json 백업 | ✅ **제거** (git history 가 백업) |
| Slop-2 LIVE_WRITABLE_PATHS dead constant | ✅ BLOCK-1 해소로 자연 해소 |
| Slop-3 workflow `-c` 이름/용도 불일치 | ✅ "sanity-only, not path guard" 주석 명시 |
| Slop-4 pre_tge_no_market vs resolved_only 시각 구분 | 🔶 Phase 3-C 구현 시 재검토 (4-state 압축 가능) |

---

## 0-b. v2 → v3 변경사항 (Codex BLOCK 4건 + FLAG 정리)

| Codex 지적 | v3 대응 |
|---|---|
| BLOCK Q1 (regex 증거 부족) | ✅ 75/75 markets, 10/10 negRisk=False 검증 결과 §3.4 추가 |
| BLOCK Q4b (CoinGecko 예산) | ✅ **30분 → 60분 cron**. 1h × 24 × 30 × 10 tokens = **7,200 calls/월** (Codex 정정), Demo 10k 대비 매우 안전. krw-listing 공유해도 합산 ~14k 수준 |
| BLOCK Q4c (branch protection) | ⚠ **사용자가 직접 확인** — §9 진입 조건 명시 |
| BLOCK Q4d (`pre_tge_resolved_only`) | ✅ UI 5-state로 확장 §4.4 |
| FLAG Q4e (negRisk) | ✅ 10/10 false 검증 (Q1과 동시) |
| FLAG Q4a (writable path CI 검증) | ✅ Actions workflow에서 git add 전 검증 함수 호출 §6 |
| FLAG schema_version 1-use | ✅ **제거** (현재 마이그레이션 호환성 필요 없음) |
| FLAG validate_schema.py 1-use | ✅ **fetch_live_data.py 인라인** |
| FLAG docs/polymarket-manifest.md 중복 | ✅ **제거** (data/projects.json 단일 매니페스트) |
| FLAG 8/9 Phase 표기 | ✅ 6 Phase로 통합 |
| FLAG 시간 8h | 12h (1.5일) — Phase 통합으로 표면 줄임 |

---

## 1. 목표

1. 콘텐츠 갱신 (2026-04-17 → 2026-05-14)
2. Polymarket 1시간 cron 라이브 갱신
3. UI 보수 (last-refresh, 5-state 분기, XSS 가드)
4. 1패스 검증 (reviewer + codex 각 1회)

---

## 2. 작업 위치

```
~/Projects/london_projects/tge-dashboard
```

---

## 3. Polymarket 스키마 (dry-run 검증 완료)

### 3.1 매니페스트 (수동, 자동 덮어쓰기 금지)

```yaml
projects:
  - ticker: "VARI"
    polymarket:
      manifest:
        event_slug: "variational-fdv-above-one-day-after-launch"
      live:                                  # 자동 갱신
        event_status: "active"               # active | resolved | partial
        event_volume24hr_usd: 0
        markets:
          - threshold_label: "$500M"
            threshold_usd: 500000000
            yes_price: 0.505
            last_traded: 0.51
            best_bid: 0.50
            best_ask: 0.51
            one_day_change: null
            closed: false
            uma_resolved: false
        pulled_at: "..."
        resolution_summary: null             # closed event 만
```

### 3.2 호출 endpoint

- 초기 manifest: `GET /public-search?q=<token>` (1회 수동)
- 운영: `GET /events/slug/<slug>` × 10 (1시간 cron)

### 3.3 Threshold 추출 (검증 완료)

```python
PATTERN = re.compile(r"FDV above \$(\d+(?:\.\d+)?)\s?([MBK]?)", re.IGNORECASE)
MULT = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000, '': 1}
```

### 3.4 dry-run 검증 결과 (Codex Q1 BLOCK 해소)

| 프로젝트 | event_slug | negRisk | closed | markets | regex_pass |
|---|---|---:|---:|---:|---:|
| Pharos | pharos-network-fdv-above-one-day-after-launch | False | True | 9 | 9 |
| Variational | variational-fdv-above-one-day-after-launch | False | False | 10 | 10 |
| Fluent | fluent-fdv-above-one-day-after-launch | False | True | 8 | 8 |
| USD.AI | usdai-fdv-above-one-day-after-launch | False | True | 14 | 14 |
| Extended | extended-fdv-above-one-day-after-launch | False | False | 7 | 7 |
| Solstice | solstice-fdv-above-one-day-after-launch | False | False | 5 | 5 |
| Ink | ink-fdv-above-one-day-after-launch | False | False | 5 | 5 |
| GRVT | grvt-fdv-above-one-day-after-launch | False | False | 7 | 7 |
| Octra | octra-fdv-above-one-day-after-launch | False | True | 5 | 5 |
| Surf | surf-fdv-above-one-day-after-launch | False | False | 5 | 5 |

**TOTAL: 75/75 markets regex pass, 10/10 negRisk=False**

---

## 4. 스키마 v3 + UI 5-state

### 4.1 metadata

```yaml
meta:
  live:
    batch_ts: "2026-05-14T12:30:00+00:00"
    source: "polymarket-gamma + coingecko"
  snapshot_date: "2026-05-14"
  polymarket_snapshot: "live (Gamma API)"
```

### 4.2 갱신 정책 화이트리스트 (v4 실제 enforcement 구현 — BLOCK-1 해소)

```python
# scripts/fetch_live_data.py 내부
LIVE_WRITABLE_PATHS = {
    'meta.live.batch_ts', 'meta.live.source', 'meta.live.partial_failure',
    'projects[].polymarket.live.event_status',
    'projects[].polymarket.live.event_volume24hr_usd',
    'projects[].polymarket.live.markets',
    'projects[].polymarket.live.pulled_at',
    'projects[].polymarket.live.resolution_summary',
    'projects[].live.current_fdv_usd',
    'projects[].live.current_price_usd',
    'projects[].live.volume_24h_usd',
    'projects[].live.source',
    'projects[].live.pulled_at',
    'projects[].live.error',
    'projects[].live.consecutive_fail_count',
}

def _flatten_diff(before, after, path='') -> set[str]:
    """before/after 재귀 비교 → 변경된 path set 반환.
    list 정규화: `projects[3].live.x` → `projects[].live.x` (인덱스 제거).
    신규/삭제 항목: 항상 차단 대상 (whitelist 외 path 로 취급)."""
    diffs = set()
    if type(before) != type(after):
        return {path or '<root>'}
    if isinstance(before, dict):
        keys = set(before) | set(after)
        for k in keys:
            sub = f"{path}.{k}" if path else k
            if k not in before or k not in after:
                diffs.add(sub)  # 신규/삭제 = 차단
            else:
                diffs |= _flatten_diff(before[k], after[k], sub)
    elif isinstance(before, list):
        norm = path + '[]'  # 인덱스 제거 정규화
        if len(before) != len(after):
            diffs.add(norm)  # 길이 변경 = 차단 (project 추가/삭제)
        else:
            for b, a in zip(before, after):
                diffs |= _flatten_diff(b, a, norm)
    else:
        if before != after:
            diffs.add(path)
    return diffs

def validate_writable_paths(before: dict, after: dict) -> None:
    """fetch 끝에서 before/after JSON 의 모든 path diff 추출.
    화이트리스트 외 path 변경 시 raise → workflow 비-제로 종료 → commit 차단."""
    illegal = _flatten_diff(before, after) - LIVE_WRITABLE_PATHS
    if illegal:
        raise RuntimeError(f"화이트리스트 외 path 변경: {illegal}")
```

**list 정규화 규칙** (BLOCK 해소):
- `projects[3].live.current_price_usd` → `projects[].live.current_price_usd` 로 정규화 후 화이트리스트와 매칭
- **신규/삭제 항목**: 차단 (projects 길이 변경, 신규 key 추가 모두 화이트리스트 외로 취급)
- 새 토큰 추가/제거는 **수동 PR** 로만 (자동 cron 이 manifest 변경 불가)

**실제 enforcement 흐름**:
1. `main()` 시작 시 `before = copy.deepcopy(json.load(open(PATH)))`
2. 모든 갱신 후 `after = json.load(open(PATH))` 재로드
3. `validate_writable_paths(before, after)` 호출 → 실패 시 RuntimeError

Actions workflow 의 inline `-c` 블록은 별개로 **sanity check (manifest 보존, batch_ts 존재) 만** 수행. **"path guard 가 아님"** 주석 명시 (Slop-3 해소).

### 4.3 UI 5-state (Q4d 해소)

```js
function uiState(p) {
  const launched = p.status === 'launched';
  const hasPrice = !!p.live?.current_price_usd;
  const pmStatus = p.polymarket?.live?.event_status;  // active | partial | resolved | null
  if (!launched && (pmStatus === 'active' || pmStatus === 'partial')) return 'pre_tge_market_active';  // partial → active 분기 흡수
  if (!launched && pmStatus === 'resolved')                            return 'pre_tge_resolved_only';  // Pharos 케이스
  if (!launched)                                                       return 'pre_tge_no_market';
  if (launched && hasPrice)                                            return 'launched_priced';
  return 'launched_no_price';
}
```

각 상태별 카드 분기:
- **pre_tge_market_active**: PM outcome 미니바 + narrative + "🎲 시장 활성"
- **pre_tge_resolved_only**: PM resolution_summary + "📊 시장 종결 (TGE 대기)" (Pharos는 PM resolved이나 토큰 미런칭일 가능성 — 실제로는 Pharos는 PM resolved + sale 완료라 launched 처리할 수도 있음, 수동 status 판단)
- **pre_tge_no_market**: narrative만 + "📅 시장 없음"
- **launched_priced**: live 가격/FDV/볼륨 + PM resolution_summary (있으면)
- **launched_no_price**: launched 표시 + ⚠ 가격 미수집

---

## 5. 단계별 계획 (6 Phase, v2의 9→6 통합)

### Phase 1: Preflight + Clone + 진단 (60분, +20분 reviewer FLAG 반영)

**1-A. 사용자 사이드 사전 확인** (Phase 1 진입 차단 조건):
```bash
# (1) branch protection
gh api /repos/londonpotato1/tge-dashboard/branches/main/protection
# 404 → protection 없음, 진행
# 200 → enforce_admins / restrictions 점검

# (2) COINGECKO_API_KEY 1-ping (krw-listing 공유 가정)
curl -s -H "x-cg-demo-api-key: <key>" https://api.coingecko.com/api/v3/ping
# {"gecko_says":"(V3) To the Moon!"} → 유효

# (3) krw-listing 실제 commit 비율 실측 (Phase 6 기대값 설정)
git -C ~/Desktop/krw-listing-dashboard log --oneline --since='1 day ago' -- data/ | wc -l
```

**1-B. 콘텐츠 사전 결정** (BLOCK-2 해소):
- **Pharos 상태 확정**: `pre_tge_resolved_only` vs `launched`. 1차 휴리스틱: CoinGecko `https://www.coingecko.com/en/coins/pharos-network` 200 + 거래소 거래 가능 → `launched`. Phase 2 researcher 입력 일관성을 위해 사전 결정.

**1-C. 로컬 작업트리 구성**:
- `git clone https://github.com/londonpotato1/tge-dashboard.git ~/Projects/london_projects/tge-dashboard`
- `index.html` 정독, `innerHTML` grep 결과 `NOTES.md` 에 기록
- ~~`data/projects.json` 백업~~ → **제거** (git history 가 백업, Slop-1 해소)

**1-D. Actions 실패 디버그 절차 사전 메모** (FLAG-6):
- 첫 cron fire 실패 시: Actions 탭 → 로그 → 흔한 패턴 (HTTP 429 / 키 누락 / git push 권한)
- `workflow_dispatch` 수동 re-fire 또는 로컬 dry-run 으로 isolate
- branch protection 차단 시: bot bypass 또는 PAT push

산출: 로컬 작업트리 + `NOTES.md` (XSS 위험점 + Pharos 결정 + krw-listing 실측치)

### Phase 2: 리서치 (researcher subagent × 1, 60분)

**FLAG-2 해소 — literal prompt block** (subagent system prompt 에 그대로 전달):

```
당신은 TGE dashboard 콘텐츠 검증 researcher 입니다. 다음 10개 프로젝트의 현재(2026-05-15) 기준 상태만 수집합니다.

대상: Pharos, Variational, Fluent, USD.AI, Extended, Solstice, Ink, GRVT, Octra, Surf
사전 확정값: Pharos status = <Phase 1-B 결정값>

각 프로젝트별 수집:
1. TGE 상태: launched / delayed / pending / canceled — 출처 URL 1~2개
2. launched 면: CoinGecko ID + 컨트랙트 주소 (체인 명시)
3. shortScore 재평가: Y/N + 1줄 근거

⚠ 강제 룰 (위반 시 환각 판정):
- 출처 URL 직접 fetch 못 한 정보는 "unknown" 기재
- CoinGecko ID: https://www.coingecko.com/en/coins/<id> 200 확인 후 기재
- 컨트랙트 주소: explorer 200 확인 후 기재
- 추측 / 유사 매칭 / "아마도" 금지
- WLFI / KAIA 같은 과거 환각 사례 절대 재발 금지

산출: docs/research-2026-05-15.md (project 별 표 형식)
```

산출: `~/Projects/london_projects/tge-dashboard/docs/research-2026-05-15.md`

### Phase 3: 스키마 + fetch_live_data.py + UI (3시간, **순차 단일 처리** — FLAG-1 해소)

v2 Phase 3+4+5 통합. **3-A → 3-B → 3-C 순차 단일 처리** ("병렬" 단어 제거, agent-directives PHASED EXECUTION 룰 준수).

3-A. **스키마 마이그레이션** (`data/projects.json`):
- `meta.live` 블록 추가 (`partial_failure` 플래그 포함 — FLAG-7)
- 10 projects 에 `polymarket.manifest.event_slug` + 빈 `live: {}` 추가
- launched 토큰만 `live.manifest` 추가
- 소스별 `pulled_at` 분리 (FLAG-7): `polymarket.live.pulled_at` 과 `live.pulled_at` 독립

3-B. **`scripts/fetch_live_data.py`** (카파시 스타일, 함수 5~7개):
```
fetch_polymarket(event_slug) -> dict
  └─ shape assertion (FLAG-4): isinstance(markets, list), outcomePrices parse 가능 등
parse_pm_markets(event_dict) -> list[dict]
  └─ regex r"FDV above \$(\d+(?:\.\d+)?)\s?([MBK]?)" 적용
fetch_coingecko_markets(ids) -> dict
fetch_defillama_prices(chain_addr_list) -> dict
apply_live(project, pm, cg, df) -> None
validate_writable_paths(before, after) -> None  # ★ §4.2 실제 enforcement (BLOCK-1)
track_consecutive_failures(slug) -> int          # ★ FLAG-5: 3회 누적 시 sys.exit(1)
main()
```

**에러 처리**:
- 개별 토큰 실패: `live.error` 기록 + 기존 값 보존 + 다음 토큰 진행
- **연속 3회 실패** (FLAG-5): `live.consecutive_fail_count` 카운터 누적. 3회 도달 시 `sys.exit(1)` → workflow fail → Actions 알림
- **부분 실패** (FLAG-7): `meta.live.partial_failure: true` 박고 commit. UI 뱃지 ⚠ 표시
- urllib + 2회 재시도 + 5초 backoff (한 줄)

3-C. **`index.html` 수정**:
- `esc()` / `safeUrl()` 헬퍼 (krw-listing copy)
- `uiState()` 분기 (Slop-4 재검토: `pre_tge_no_market` vs `pre_tge_resolved_only` 시각 구분 없으면 4-state 압축)
- last-refresh 뱃지 — **stale 임계값 90분** (FLAG-3: cron 60 + Pages lag 30)
- `partial_failure` 시 별도 ⚠ 표시
- PM outcome 미니바
- 480px 모바일 CSS
- `</` → `<\/` script breakout

### Phase 4: Actions workflow + 멱등성 검증 (45분)
- `.github/workflows/refresh-data.yml` 작성 (1시간 cron, krw-listing 패턴):
  ```yaml
  schedule: [{ cron: '0 * * * *' }]   # ← 30분 → 1시간 (Q4b)
  steps:
    - run: python3 scripts/fetch_live_data.py
    - run: |                          # sanity-only — NOT path guard (실제 guard 는 §4.2 fetch 스크립트 내부)
        python3 -c "
        import json
        d = json.load(open('data/projects.json'))
        for p in d['projects']:
          assert 'polymarket' in p and 'manifest' in p['polymarket']
          assert 'event_slug' in p['polymarket']['manifest']
        assert d['meta']['live']['batch_ts']
        print('sanity ok')
        "
    - run: git add data/projects.json && (git diff --cached --quiet && echo skip || git commit -m "...")
  ```
- `python3 scripts/fetch_live_data.py` 2회 → 미세 변동만
- `python3 -m http.server 8000` → 5-state 시각 확인

### Phase 5: 검증 (1패스, 75분)
5-A. **reviewer subagent** (1회):
- LIVE_WRITABLE_PATHS 외 필드 변경 없음
- 5-state UI 분기 작동
- XSS 가드 모든 데이터 출력에 적용
- 카파시 슬롭 체크 (1-use 헬퍼/클래스 양산 명시 판정)

5-B. FLAG/BLOCK 수정 + 재검증

5-C. **codex-rescue 메타 검토** (1회):
- reviewer 누락 영역
- threshold 정규식 edge case
- resolved 분기 robustness

5-D. **보안**:
- `pre-push` 스킬 또는 manual grep
- `git secrets`로 키 누출 검사
- `innerHTML` 가드 누락 grep

### Phase 6: 배포 + 모니터링 (30분 + 24h 백그라운드)
- 분리 commit: (a) schema (b) script + workflow (c) UI (d) content
- `git push` → Pages 60초
- `curl -I https://londonpotato1.github.io/tge-dashboard/?sort=fdv` → 200
- Actions 탭 → `workflow_dispatch` 수동 fire → 첫 라이브 commit 확인
- 다음 시간 boundary 대기 → cron 자동 fire 확인

**24h 모니터링** (백그라운드):
- commit 빈도 (시간당 1회 정상, "no changes" skip 비율 확인)
- API 429 발생 여부

---

## 6. 리스크 14건 (v2 동일, 1건 보강)

(v2 §6 그대로 + #15 추가)

| # | 리스크 | 완화 |
|---|---|---|
| 15 | **CI에서 writable path 검증 누락** | 실제 path guard 는 `fetch_live_data.py` 내부 `validate_writable_paths(before, after)` 로 수행 (§4.2). Actions workflow 의 inline `-c` 는 sanity-only (manifest 보존 + batch_ts 존재 확인) — path guard 아님 |

---

## 7. 시간 (Codex Q2 FLAG 반영)

| Phase | 시간 |
|---|---|
| 1. Preflight + Clone | 60분 |
| 2. 리서치 | 60분 |
| 3. 스키마 + 스크립트 + UI (순차 3-A→3-B→3-C) | 180분 |
| 4. Workflow + 멱등성 | 45분 |
| 5. 검증 (reviewer + codex) | 75분 |
| 6. 배포 | 30분 |
| (백그라운드) 24h 모니터링 | — |
| **소계** | **약 7h 집중** |
| 예비 (edge case / API 이슈) | +3h |
| **최대 추정** | **10~12h (1.5일)** |

---

## 8. 의사결정 (확정)

| Q | 답변 |
|---|---|
| Q1 작업 위치 | `~/Projects/london_projects/tge-dashboard` |
| Q2 라이브 범위 | Polymarket + launched 가격 |
| Q3 빌드 방식 | 단일 `index.html` + JSON fetch |
| Q4 리서치 깊이 | launched/Polymarket 상태만 |
| Q5 토큰 수 | 10개 고정 |
| Q6 카드 디자인 차용 | 김프/캔들 안 함 |
| Q7 갱신 주기 | **1시간** (CoinGecko 예산) |
| Q8 branch protection | **사용자 직접 확인** (Phase 1 진입 전) |
| Q9 CoinGecko 키 | **krw-listing 공유** (1시간 cron → **7,200 calls/월** 안전, Demo 10k 한도 대비) |
| Q10 PM slug 검증 | Phase 3-A에서 manual one-time (dry-run 결과 이미 확정) |
| Q11 TGE 자동 전환 | **수동 PR** (위험 회피) |

---

## 9. 진입 조건 (reviewer FLAG-6 보강)

Phase 1 시작 전:
1. ✅ Q1~Q11 모두 확정
2. ⏳ **branch protection 확인** (`gh api /repos/londonpotato1/tge-dashboard/branches/main/protection`)
3. ⏳ `gh auth status` 인증 확인
4. ⏳ **`COINGECKO_API_KEY` 1-ping** (`/api/v3/ping` 200 응답)
5. ⏳ **krw-listing skip 비율 실측** (`git log --since='1 day ago' -- data/`)
6. ⏳ **Pharos 상태 사전 결정** (`pre_tge_resolved_only` 또는 `launched`)

---

## 10. 산출물 (v4 — Slop-1: projects.v1.json 제거)

```
~/Projects/london_projects/tge-dashboard/
├── index.html                          (수정: esc/safeUrl/uiState/stale 90분/partial_failure ⚠)
├── data/
│   └── projects.json                   (스키마 v4: manifest 박힘 + meta.live.partial_failure)
├── scripts/
│   └── fetch_live_data.py              (신규: validate_writable_paths 실제 구현 + shape assertion + 3회 실패 추적)
├── docs/
│   └── research-2026-05-15.md          (researcher 산출)
├── .github/workflows/refresh-data.yml  (1시간 cron + sanity-only 주석)
├── README.md                           (수정)
└── DEPLOY.md                           (수정)

# git history 가 projects.json 백업 역할 (별도 *.v1.json 파일 X)
```
