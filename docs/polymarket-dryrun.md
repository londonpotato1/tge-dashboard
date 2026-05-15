# Polymarket Gamma API Dry-Run 결과 (2026-05-14)

> 대상: tge-dashboard 10개 프로젝트
> 목적: event/market 구조 확정 + 라이브 필드 식별

---

## 1. 올바른 endpoint

| 용도 | endpoint |
|---|---|
| ❌ slug 검색 (작동 안 함) | `GET /events?slug_contains=X` |
| ❌ keyword 검색 (작동 안 함) | `GET /events?q=X` |
| ✅ **풀텍스트 검색** | `GET /public-search?q=X&limit_per_type=N` |
| ✅ event 직접 조회 | `GET /events/slug/<slug>` |
| ✅ event tag/필터 | `GET /events?tag=crypto&active=true&closed=false` |

응답: `{ "events": [...] }` (events 안에 markets[] 임베드)

---

## 2. 10개 프로젝트 Polymarket 시장 매니페스트 (확인 완료)

| 프로젝트 | FDV event slug | 상태 | markets | 추가 event (TGE 일정) |
|---|---|---|---:|---|
| Pharos | `pharos-network-fdv-above-one-day-after-launch` | **resolved** | 9 | `pharos-public-sale-total-commitments` (closed) |
| Variational | `variational-fdv-above-one-day-after-launch` | **active** | 10 | `will-variational-launch-a-token-in-2025` (3 open) |
| Fluent | `fluent-fdv-above-one-day-after-launch` | **resolved** | 8 | `fluent-public-sale-total-commitments` (closed) |
| USD.AI | `usdai-fdv-above-one-day-after-launch` | **resolved** | 14 | `what-day-will-the-usdai-token-launch-be` (closed) |
| Extended | `extended-fdv-above-one-day-after-launch` | **active** | 7 | `will-extended-launch-a-token-by` (3 open) |
| Solstice | `solstice-fdv-above-one-day-after-launch` | **active** | 5 | `will-solstice-launch-a-token-by` (3 open) |
| Ink | `ink-fdv-above-one-day-after-launch` | **active** | 5 | (none) |
| GRVT | `grvt-fdv-above-one-day-after-launch` | **active** | 7 | `will-grvt-launch-a-token-by` (3 open) |
| Octra | `octra-fdv-above-one-day-after-launch` | **resolved** | 5 | (none) |
| Surf | `surf-fdv-above-one-day-after-launch` | **active** | 5 | (none) |

**합계**: 6/10 active, 4/10 resolved (Pharos / Fluent / USD.AI / Octra → 이미 TGE 완료)

**slug 패턴 일관성**: `{project-slug}-fdv-above-one-day-after-launch` (10/10 hit). 자동 검색이 아닌 **수동 매니페스트 유지** 권장 (`data/projects.json`에 `polymarket.event_slug` 박아둠).

---

## 3. Event 응답 구조 (확정)

```yaml
event:
  id: "403977"
  slug: "pharos-network-fdv-above-one-day-after-launch"
  ticker: "..."
  title: "Pharos Network FDV above ___ one day after launch?"
  startDate / endDate / creationDate / updatedAt
  active: bool             # 시장 활성 (배포)
  closed: bool             # 전체 종결 (이벤트 레벨)
  archived: bool
  negRisk: bool            # neg-risk multi-outcome 시장 여부 (FDV는 false)
  volume / volume24hr / volume1wk / volume1mo: number
  liquidity: number
  openInterest: number
  markets: [Market]        # ★ threshold당 1개
```

## 4. Market 응답 구조 (threshold당 1개)

```yaml
market:
  id: "..."
  question: "Variational FDV above $500M one day after launch?"
  slug: "variational-fdv-above-500m-..."
  conditionId: "0x..."     # 정산 키
  outcomes: '["Yes","No"]'  # ⚠ stringified JSON
  outcomePrices: '["0.505","0.495"]'  # ⚠ stringified, 호가 mid
  lastTradePrice: 0.51     # ✅ raw float
  bestBid: 0.5
  bestAsk: 0.51
  oneDayPriceChange: 0.005 # null 가능
  active: bool
  closed: bool
  acceptingOrders: bool
  groupItemThreshold: "3"  # ⚠ stringified int (정렬 인덱스, NOT 달러값)
  groupItemTitle: "..."
  closedTime: "2026-04-29 23:34:32+00"  # closed일 때만
  umaResolutionStatus: "resolved" | "..."
  endDate / startDate
  volume / volumeNum
  clobTokenIds: '[...]'    # CLOB 토큰 (라이브 호가용)
```

---

## 5. 핵심 라이브 갱신 필드 (최종 확정)

| 필드 | 의미 | 비고 |
|---|---|---|
| `event.active`, `event.closed` | 전체 시장 상태 | resolved 시 카드 시각 분기 |
| `event.volume24hr` | 24h 거래량 | UI 신뢰도 표시 |
| `market.outcomePrices[0]` | Yes 확률 (parsed) | **라이브 핵심** |
| `market.lastTradePrice` | 최근 체결가 | outcomePrices 보다 신선 |
| `market.bestBid` / `bestAsk` | 호가 스프레드 | 유동성 신호 |
| `market.oneDayPriceChange` | 24h 변화 | 트렌드 표시 |
| `market.umaResolutionStatus` | UMA 정산 상태 | `resolved` 시 결과 표기 |
| `market.closedTime` | 정산 시각 | resolved 시 표시 |

**Threshold 라벨 추출**: `groupItemThreshold`는 정렬 인덱스만 제공. 실제 달러 임계값(`$100M`, `$500M` 등)은 **`market.question` 정규식**으로 추출 필요. 패턴: `r'FDV above \$(\d+(?:\.\d+)?[MB])'`.

---

## 6. Resolved 결과 해석 (Pharos 사례)

| threshold | outcomePrices | 해석 |
|---|---|---|
| 0~5 | `["1", "0"]` | Yes 정산 → 임계값 이상 |
| 6~8 | `["0", "1"]` | No 정산 → 임계값 미달 |

Resolved FDV 추정: 가장 큰 Yes-정산 threshold ($X)와 가장 작은 No-정산 threshold ($Y) 사이.

**UI 표시 예**: `"FDV resolved: $X ~ $Y (Polymarket, 2026-04-29)"`

---

## 7. 데이터 신선도 & 호출 빈도

- Polymarket 인증 무필요, rate limit 관대 (정확한 한계 미공개)
- 한 번 호출 = 1 event (modal 9-14 markets 포함)
- 10 events × `public-search` 1회씩 호출 (slug 직접 조회로 단축 가능: `/events/slug/<slug>` 10회)
- 30분 cron 1회 = 10 API call → 안전권
- 24h 변동은 `oneDayPriceChange` 사용, 폴링 빈도 1회/30분으로 충분

---

## 8. 계획서 v1에서 수정이 필요한 항목

1. **스키마**: `polymarket.event_slug` 만 매니페스트 유지. `outcomes`는 question에서 dollar threshold 추출 후 `[ { threshold_label, threshold_index, yes_price, last_traded, ... } ]` 배열로 구조화.
2. **stringified JSON 처리**: `outcomes` / `outcomePrices` 둘 다 parse 필요.
3. **Resolved 처리**: `event.closed && event.markets[].outcomePrices` 통과 패턴 분석 → FDV 범위 추론.
4. **`will-X-launch-a-token-by` 보조 event**: TGE 일정 prediction 표시용 (선택, MVP 제외 가능).
5. **`acceptingOrders == false` & `closed == false`**: 정산 대기 상태 (UMA 분쟁/oracle). UI에 "정산 진행 중" 표시.
6. **endpoint 단순화**: `public-search`는 검색용. 매니페스트 확정 후 운영은 **`/events/slug/<slug>`** 직접 호출 (검색 잡음 제거 + 응답 작음).
