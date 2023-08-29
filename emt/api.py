from typing import Any


class TradeApi:

    def login(self, username: str, password: str, duration: int):
        raise NotImplementedError

    def query_asset(self):
        raise NotImplementedError

    def query_position(self):
        raise NotImplementedError

    def query_orders(self):
        """ 请求查询报单 """
        raise NotImplementedError

    def query_trades(self):
        """ 请求查询成交 """
        raise NotImplementedError

    def query_history_orders(self):
        """ 请求查询历史报单 """
        raise NotImplementedError

    def query_history_trades(self):
        """ 请求查询历史成交 """
        raise NotImplementedError

    def insert_order(self, symbol_code: str, side: Any, price: float, qty: int):
        raise NotImplementedError

    def cancel_order(self, code: str) -> bool:
        raise NotImplementedError
