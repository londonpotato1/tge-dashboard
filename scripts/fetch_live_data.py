#!/usr/bin/env python3
"""TGE Dashboard live data fetcher.

Polymarket Gamma + CoinGecko 에서 라이브 데이터 수집해 projects.json 의
LIVE_WRITABLE_PATHS 만 갱신. 1시간 cron 실행 가정.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request
from urllib.parse import quote

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'projects.json'

LIVE_WRITABLE_PATHS = {
    'meta.live.batch_ts',
    'meta.live.source',
    'meta.live.partial_failure',
    'projects[].polymarket.live.event_status',
    'projects[].polymarket.live.event_volume24hr_usd',
    'projects[].polymarket.live.markets[]',
    'projects[].polymarket.live.markets[].threshold_label',
    'projects[].polymarket.live.markets[].threshold_usd',
    'projects[].polymarket.live.markets[].yes_price',
    'projects[].polymarket.live.markets[].last_traded',
    'projects[].polymarket.live.markets[].closed',
    'projects[].polymarket.live.pulled_at',
    'projects[].polymarket.live.resolution_summary',
    'projects[].polymarket.live.error',
    'projects[].live.current_fdv_usd',
    'projects[].live.current_price_usd',
    'projects[].live.volume_24h_usd',
    'projects[].live.source',
    'projects[].live.pulled_at',
    'projects[].live.error',
    'projects[].live.consecutive_fail_count',
}

POLYMARKET_BASE = "https://gamma-api.polymarket.com/events/slug/"
COINGECKO_BASE = "https://api.coingecko.com/api/v3/coins/markets"
THRESHOLD_RE = re.compile(r"FDV above \$(\d+(?:\.\d+)?)\s?([MBK]?)")
FAIL_THRESHOLD = 3
USER_AGENT = "tge-dashboard-cron/1.0 (+https://github.com/londonpotato1/tge-dashboard)"


def http_get(url: str, retries: int = 2):
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = request.Request(url, headers={'User-Agent': USER_AGENT})
            with request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except (error.HTTPError, error.URLError, json.JSONDecodeError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(5)
    raise RuntimeError(f"GET {url} failed: {last_err}")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')


def fetch_polymarket(event_slug: str) -> dict:
    data = http_get(POLYMARKET_BASE + quote(event_slug))
    if not isinstance(data.get('markets'), list):
        raise RuntimeError(f"polymarket {event_slug}: markets not list")
    return data


def parse_pm_markets(event: dict) -> list:
    out = []
    for m in event.get('markets', []):
        match = THRESHOLD_RE.search(m.get('question', ''))
        if not match:
            continue
        val, unit = match.groups()
        mult = {'K': 1e3, 'M': 1e6, 'B': 1e9, '': 1}[unit]
        threshold_usd = float(val) * mult
        prices_raw = m.get('outcomePrices') or '["0","0"]'
        try:
            prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
            yes_price = float(prices[0])
        except (json.JSONDecodeError, IndexError, ValueError, TypeError):
            yes_price = None
        out.append({
            'threshold_label': f"${val}{unit}",
            'threshold_usd': threshold_usd,
            'yes_price': yes_price,
            'last_traded': m.get('lastTradePrice'),
            'closed': bool(m.get('closed')),
        })
    out.sort(key=lambda x: x['threshold_usd'])
    return out


def fetch_coingecko(coin_ids: list) -> dict:
    if not coin_ids:
        return {}
    url = f"{COINGECKO_BASE}?vs_currency=usd&ids={quote(','.join(coin_ids))}&per_page=50"
    arr = http_get(url)
    if not isinstance(arr, list):
        return {}
    return {item['id']: item for item in arr if isinstance(item, dict) and item.get('id')}


def apply_pm(project: dict, event: dict) -> None:
    pm_live = project['polymarket']['live']
    is_closed = bool(event.get('closed'))
    markets = parse_pm_markets(event)
    any_active = any(not m['closed'] for m in markets)
    if is_closed and markets and not any_active:
        status = 'resolved'
    elif is_closed or (markets and not any_active):
        status = 'partial'
    else:
        status = 'active'
    pm_live['event_status'] = status
    pm_live['event_volume24hr_usd'] = event.get('volume24hr')
    pm_live['markets'] = markets
    pm_live['pulled_at'] = now_iso()
    pm_live['error'] = None
    if status == 'resolved':
        won = [m for m in markets if (m.get('yes_price') or 0) >= 0.99]
        if won:
            top = max(won, key=lambda m: m['threshold_usd'])
            pm_live['resolution_summary'] = f"FDV ≥ {top['threshold_label']} resolved Yes"
        else:
            pm_live['resolution_summary'] = "all thresholds resolved No"
    else:
        pm_live['resolution_summary'] = None


def apply_cg(project: dict, cg_item) -> None:
    if 'live' not in project:
        return
    live = project['live']
    fail = live.get('consecutive_fail_count') or 0
    if not cg_item:
        live['error'] = 'coingecko: id not found'
        live['consecutive_fail_count'] = fail + 1
        live['pulled_at'] = now_iso()
        return
    live['current_price_usd'] = cg_item.get('current_price')
    live['current_fdv_usd'] = cg_item.get('fully_diluted_valuation') or cg_item.get('market_cap')
    live['volume_24h_usd'] = cg_item.get('total_volume')
    live['source'] = 'coingecko'
    live['pulled_at'] = now_iso()
    live['error'] = None
    live['consecutive_fail_count'] = 0


def _flatten_diff(before, after, path=''):
    diffs = set()
    if type(before) != type(after):
        return {path or '<root>'}
    if isinstance(before, dict):
        keys = set(before) | set(after)
        for k in keys:
            sub = f"{path}.{k}" if path else k
            if k not in before or k not in after:
                diffs.add(sub)
            else:
                diffs |= _flatten_diff(before[k], after[k], sub)
    elif isinstance(before, list):
        norm = path + '[]'
        if len(before) != len(after):
            diffs.add(norm)
        else:
            for b, a in zip(before, after):
                diffs |= _flatten_diff(b, a, norm)
    else:
        if before != after:
            diffs.add(path)
    return diffs


def validate_writable(before: dict, after: dict) -> None:
    illegal = _flatten_diff(before, after) - LIVE_WRITABLE_PATHS
    if illegal:
        raise RuntimeError(f"화이트리스트 외 path 변경: {sorted(illegal)}")


def main():
    raw = DATA_PATH.read_text()
    before = json.loads(raw)
    data = json.loads(raw)

    partial = False

    for p in data['projects']:
        slug = p['polymarket']['manifest']['event_slug']
        try:
            event = fetch_polymarket(slug)
            apply_pm(p, event)
        except Exception as e:
            partial = True
            p['polymarket']['live']['error'] = str(e)[:200]
            p['polymarket']['live']['pulled_at'] = now_iso()

    launched = [
        p for p in data['projects']
        if (p.get('live') or {}).get('manifest', {}).get('coingecko_id')
    ]
    cg_ids = [p['live']['manifest']['coingecko_id'] for p in launched]
    try:
        cg = fetch_coingecko(cg_ids)
    except Exception as e:
        partial = True
        cg = {}
        print(f"coingecko batch failed: {e}", file=sys.stderr)

    for p in launched:
        apply_cg(p, cg.get(p['live']['manifest']['coingecko_id']))

    fatal_tokens = [
        p['name'] for p in data['projects']
        if ((p.get('live') or {}).get('consecutive_fail_count') or 0) >= FAIL_THRESHOLD
    ]

    # idempotency: timestamp 외 실데이터 변경 없으면 batch_ts / pulled_at 도 보존
    def strip_ts(obj):
        if isinstance(obj, dict):
            return {k: strip_ts(v) for k, v in obj.items() if k not in ('batch_ts', 'pulled_at')}
        if isinstance(obj, list):
            return [strip_ts(x) for x in obj]
        return obj

    skipped = strip_ts(before) == strip_ts(data)
    if skipped:
        print("no live data change — keeping previous timestamps, skipping write")
    else:
        data['meta']['live']['batch_ts'] = now_iso()
        data['meta']['live']['source'] = 'polymarket-gamma + coingecko'
        data['meta']['live']['partial_failure'] = partial or bool(fatal_tokens)
        validate_writable(before, data)
        DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f"fetch_live ok. partial_failure={partial or bool(fatal_tokens)}")

    # write 후 exit — 그래야 disk 의 consecutive_fail_count 가 진행되고
    # 다음 run 이 동일 상태에서 반복되는 영구 정체를 방지한다.
    if fatal_tokens:
        print(f"FATAL: {fatal_tokens} consecutive_fail_count >= {FAIL_THRESHOLD}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
