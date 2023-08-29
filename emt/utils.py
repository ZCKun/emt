import requests
import math
from typing import Optional


def double_equal(a, b) -> bool:
    return math.fabs(a - b) < 1e-6


def get_float(data: dict, key: str) -> float:
    if v := data[key].strip():
        return float(v)
    return .0


def get_int(data: dict, key: str) -> int:
    if v := data[key].strip():
        return int(v)
    return 0


def query_snapshot(symbol_code: str, market: str) -> Optional[dict]:
    url = 'https://emhsmarketwg.eastmoneysec.com/api/SHSZQuoteSnapshot'
    params = {
        'id': symbol_code.strip(),
        'market': market
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.0.0 Safari/537.36'
    }
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        print(f"fetch snapshot for {symbol_code}.{market} fail, code={resp.status_code}, response={resp.text}")
        return None

    return resp.json()


def get_last_price(symbol_code: str, market: str) -> float:
    ret = query_snapshot(symbol_code, market)
    if ret is None or 'status' not in ret or ret['status'] != 0:
        return float('nan')

    return get_float(ret['realtimequote'], 'currentPrice')


# def test():
#     assert double_equal(get_last_price('000001', 'SZ'), 11.31)
#     assert double_equal(get_last_price('603121', 'SH'), 8.01)
#     assert math.isnan(get_last_price('000001', 'SH'))
#     print('test pass')
#
#
# test()
