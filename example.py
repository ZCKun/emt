import math

from emt import EMTTrade, Direction, InstrumentID,\
    MarketType, get_last_price


def test():
    baskets = {'300485': 'SZ'}

    t = EMTTrade()
    resp = t.login('<username>', '<password>')
    print(resp)
    if not resp:
        return
    positions = t.query_position()
    print(positions)
    for pos in positions:
        if pos.symbol_code in baskets:
            del baskets[pos.symbol_code]

    print(t.account)
    assert t.account.asset.available_funds > 0, 'insufficient available funds in the account'
    for code, market in baskets.items():
        last_price = get_last_price(code, market)
        if math.isnan(last_price):
            print(f"failed to fetch the last price for {code}.{market}, the last price is 'nan'")
            continue
        ins_id = InstrumentID(code, MarketType.SZE if market == 'SZ' else MarketType.SSE)
        order = t.insert_order(ins_id, Direction.Buy, last_price, 100)
        print(f'insert_order for {code}.{market}: ', order)
        # print(f'cancel {order.cancel()}')

    # t.insert_order('600745', Direction.Buy, 40.3, 100)
    orders = t.query_orders()
    for order in orders:
        print(order)
    #     if order.is_alive():
    #         order.cancel()


if __name__ == '__main__':
    test()
