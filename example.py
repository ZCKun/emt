import dataclasses
import math

from emt import EMTTrade, Direction, InstrumentID, \
    MarketType, get_last_price


@dataclasses.dataclass
class EMTConfig:
    username: str
    password: str
    baskets: dict


class EMTTradeDemo:

    def __init__(self, cfg: EMTConfig):
        self._cfg = cfg
        self._emt_trade = EMTTrade()
        self._is_ready: bool = False
        self._login()

    def _login(self):
        resp = self._emt_trade.login(self._cfg.username, self._cfg.password)
        print(f"login response: [{resp}]")
        if not resp:
            return

        # 检查账户可用资金
        account_is_ok = self._emt_trade.account.asset.available_funds > 0
        if not account_is_ok:
            print("insufficient available funds in the account")
            return
        self._is_ready = True

    def _query_position(self):
        """查询持仓，并清理篮子中已有持仓的标的"""
        positions = self._emt_trade.query_position()
        print(positions)
        for pos in positions:
            if pos.symbol_code in self._cfg.baskets:
                del self._cfg.baskets[pos.symbol_code]

    def _place_order_with_baskets(self):
        if not self._is_ready:
            return
        # 按篮子股票列表下单
        for code, market in self._cfg.baskets.items():
            last_price = get_last_price(code, market)
            if math.isnan(last_price):
                print(f"failed to fetch the last price for {code}.{market}, the last price is 'nan'")
                continue
            ins_id = InstrumentID(code, MarketType.SZE if market == 'SZ' else MarketType.SSE)
            order = self._emt_trade.insert_order(ins_id, Direction.Buy, last_price, 100)
            print(f'insert_order for {code}.{market}: ', order)

    def _query_order_list_and_cancel(self):
        # 查询所有委托
        orders = self._emt_trade.query_orders()
        for order in orders:
            print(order)
            # 如果订单还存活就撤单
            if order.is_alive():
                ret = order.cancel()
                order_name = f"{order.symbol_code}-{order.side.name}@{order.order_id}"
                print(f"{order_name} 撤单{'成功' if ret else '失败'}")

    def start(self):
        self._query_position()
        self._place_order_with_baskets()
        self._query_order_list_and_cancel()


def main():
    cfg = EMTConfig('', '', {})
    demo = EMTTradeDemo(cfg)
    demo.start()


if __name__ == '__main__':
    main()
