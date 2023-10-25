import datetime
import re
import random
import requests

from typing import Optional, Any
from ddddocr import DdddOcr
from .log import logger
from .api import TradeApi
from .emt_trade_encrypt import EMTradeEncrypt
from .types import Response, response_deserialize, \
    Position, position_deserialize, \
    Asset, Account, account_deserialize, \
    OrderInfo, order_deserialize, \
    Direction, InstrumentID, MarketType, OrderStatus


class EMTTrade(TradeApi):

    def __init__(self):
        super().__init__()
        self._emt_trade_encrypt = EMTradeEncrypt()
        self._em_validatekey: str = ''
        self._base_headers: dict = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36',
            'Origin': 'https://jywg.18.cn',
            'Host': 'jywg.18.cn'
        }
        self._account: Optional[Account] = None
        self._session: requests.Session = requests.Session()
        self._ocr = DdddOcr(show_ad=False)
        self._orders = {}
        self._urls: dict = {
            'login': 'https://jywg.18.cn/Login/Authentication?validatekey=',
            'query_asset_and_pos': 'https://jywg.18.cn/Com/queryAssetAndPositionV1?validatekey=',
            'query_orders': 'https://jywg.18.cn/Search/GetOrdersData?validatekey=',
            'query_trades': 'https://jywg.18.cn/Search/GetDealData?validatekey=',
            'query_his_orders': 'https://jywg.18.cn/Search/GetHisOrdersData?validatekey=',
            'query_his_trades': 'https://jywg.18.cn/Search/GetHisDealData?validatekey=',
            'query_funds_flow': 'https://jywg.18.cn/Search/GetFundsFlow?validatekey=',
            'query_positions': 'https://jywg.18.cn/Search/GetStockList?validatekey=',
            'insert_order': 'https://jywg.18.cn/Trade/SubmitTradeV2?validatekey=',
            'cancel_order': 'https://jywg.18.cn/Trade/RevokeOrders?validatekey=',
        }

    def query_asset(self) -> Asset:
        """ 请求查询资产 """
        self.query_asset_and_position()
        return self._account.asset

    def query_position(self) -> list[Position]:
        """ 请求查询投资者持仓 """
        self.query_asset_and_position()
        return self._account.positions

    @property
    def account(self) -> Account:
        return self._account

    def login(
        self,
        username: str,
        password: str,
        duration: int = 30
    ) -> Optional[Response]:
        """ 登录

        :param username: 用户名
        :param password: 密码(明文)
        :param duration: 在线时长(分钟)
        :return:
        """
        if (ret := self._get_captcha_code()) is None:
            return
        random_num, code = ret

        headers = self._base_headers.copy()
        headers['X-Requested-With'] = 'XMLHttpRequest'
        headers['Referer'] = 'https://jywg.18.cn/Login?el=1&clear=&returl=%2fTrade%2fBuy'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        url = self._urls['login']
        data = {
            'userId': username.strip(),
            'password': self._emt_trade_encrypt.encrypt(password.strip()),
            'randNumber': random_num,
            'identifyCode': code,
            'duration': duration,
            'authCode': '',
            'type': 'Z',
            'secInfo': '',
        }
        resp = self._session.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            logger.error(f"user [{username}] login fail, code={resp.status_code}, response={resp.text}")
            return

        data = resp.json()
        try:
            resp = response_deserialize(data)
            if resp.status == 0 and resp.message.strip() == '':
                logger.info(f"login success for {resp.data[0]['khmc']}({username})")
                self._get_em_validatekey()
                if self._em_validatekey:
                    self.query_asset_and_position()
            return resp
        except KeyError as e:
            logger.error(f"param data found exception:[{e}], [data={data}]")
            return None

    def _get_em_validatekey(self):
        """ 获取 em_validatekey """
        url = 'https://jywg.18.cn/Trade/Buy'
        resp = self._session.get(url, headers=self._base_headers)
        if resp.status_code != 200:
            logger.error(f'get em validatekey fail, code={resp.status_code}, response={resp.text}')
            return

        match_result = re.findall(r'id="em_validatekey" type="hidden" value="(.*?)"', resp.text)
        if match_result:
            self._em_validatekey = match_result[0].strip()
            logger.debug(f"success to get em_validatekey={self._em_validatekey}")

    def _query_something(
        self,
        tag: str,
        count: int = 100,
        data: Optional[dict] = None
    ) -> Optional[requests.Response]:
        """ 通用查询函数

        :param tag: 请求类型
        :param count: 查询数量，可选
        :param data: 请求提交数据，可选
        :return:
        """
        assert self._em_validatekey, "em_validatekey is empty"
        assert self._session is not None, "session is None"
        assert tag in self._urls, f"{tag} not in url list"
        url = self._urls[tag] + self._em_validatekey
        if data is None:
            if count <= 0:
                count = 100
            elif count > 1000:
                count = 1000
            data = {
                'qqhs': count,
                'dwc': '',
            }
        headers = self._base_headers.copy()
        headers['X-Requested-With'] = 'XMLHttpRequest'
        logger.debug(f"(tag={tag}), (data={data}), (url={url})")
        resp = self._session.post(url, headers=headers, data=data)
        if resp.status_code != 200:
            logger.error(f"use [{tag}] to query fail, code={resp.status_code}, response={resp.text}")
            return None

        logger.debug(resp.text)
        # return response_deserialize(resp.json())
        return resp

    def _get_captcha_code(self) -> Optional[tuple[float, Any]]:
        """ get random number and captcha code """
        random_num = random.random()
        resp = self._session.get(f'https://jywg.18.cn/Login/YZM?randNum={random_num}', headers=self._base_headers)
        if resp.status_code != 200:
            logger.error(f"get captcha code fail, code={resp.status_code}, response={resp.text}")
            return None

        with open('.jywg_code.jpg', 'wb') as f:
            f.write(resp.content)
        code = self._ocr.classification(resp.content)
        logger.debug(f'random_num={random_num}, code={code}')
        if code:
            try:
                return random_num, int(code)
            except Exception as e:
                logger.error(f'get_captcha_code found exception: {e}, ocr result={code}')
                return self._get_captcha_code()
        return None

    def query_asset_and_position(self):
        resp = self._query_something('query_asset_and_pos')
        try:
            resp = response_deserialize(resp.json())
        except Exception as e:
            logger.error(f"request response deserialize found exception {e}")
            return

        if resp and resp.is_ok():
            self._account = account_deserialize(resp.data[0])

    def query_orders(self):
        resp = self._query_something('query_orders')
        try:
            resp = response_deserialize(resp.json())
        except Exception as e:
            logger.error(f"request response deserialize found exception {e}")
            return

        orders = []
        if resp and resp.is_ok():
            for i in resp.data:
                order_info = order_deserialize(i)
                order_info._api = self
                orders.append(order_info)
        return orders

    def query_trades(self):
        self._query_something('query_trades')

    def query_history_orders(self):
        self._query_something('query_his_orders')

    def query_history_trades(self):
        self._query_something('query_his_trades')

    def query_funds_flow(self):
        self._query_something('query_funds_flow')

    def insert_order(
        self,
        ins_id: InstrumentID,
        side: Direction,
        price: float,
        qty: int
    ) -> Optional[OrderInfo]:
        data = {
            'stockCode': ins_id.symbol_code,
            'tradeType': 'B' if side == Direction.Buy else 'S',
            'zqmc': '',
            'market': 'HA' if ins_id.market_type == MarketType.SSE else 'SA',
            'price': price,
            'amount': qty,
        }
        resp = self._query_something('insert_order', data=data)
        try:
            resp = response_deserialize(resp.json())
        except Exception as e:
            logger.error(f"request response deserialize found exception {e}")
            return

        logger.debug(f"insert_order> {resp}")
        if resp is None or not resp.is_ok() or not resp.data:
            return None

        data = resp.data[0]
        order = OrderInfo(
            symbol_code=ins_id.symbol_code,
            quotation_time=None,
            insert_time=datetime.datetime.now(),
            order_id=data['Wtbh'],
            insert_qty=qty,
            canceled_qty=0,
            insert_price=price,
            trade_price=float('nan'),
            status=OrderStatus.INSERT_SUBMITTED,
            side=side,
            _api=self
        )
        return order

    def cancel_order(self, code: str) -> bool:
        data = dict(revokes=code.strip())
        resp = self._query_something('cancel_order', data=data)
        try:
            resp = response_deserialize(resp.json())
            logger.error(f"cancel order {code} fail, message={resp}")
            return False
        except Exception:
            pass

        logger.debug(f"cancel_order> {resp.text}")
        return True
