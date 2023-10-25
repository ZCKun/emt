import enum
import datetime

from typing import Any, Optional
from dataclasses import dataclass
from .utils import get_int, get_float
from .api import TradeApi


class OrderStatus(enum.IntEnum):
    UNKNOWN = 0
    INSERT_SUBMITTED = 1
    INSERT_ACCEPTED = 2
    FULL_TRADED = 3
    PART_TRADED = 4
    CANCELED = 5
    REJECTED = 6


_order_status_map = {
    '已成': OrderStatus.FULL_TRADED,
    '部成': OrderStatus.PART_TRADED,
    '已受理': OrderStatus.INSERT_ACCEPTED,
}


def order_status_parser(string: str) -> OrderStatus:
    if string in ['未报', '已报', '待报']:
        return OrderStatus.INSERT_SUBMITTED
    if string not in _order_status_map:
        return OrderStatus.UNKNOWN
    return _order_status_map[string]


class MarketType(enum.IntEnum):
    SZE = 1
    SSE = 2


@dataclass
class InstrumentID:
    symbol_code: str
    market_type: MarketType


class Order:

    def __init__(self):
        pass

    def cancel(self):
        pass


class Direction(enum.IntEnum):
    Buy = 0
    Sell = 1


@dataclass
class Response:
    message: str
    status: int
    error_code: str
    data: Any

    def is_ok(self) -> bool:
        return not self.message and self.status == 0


def response_deserialize(data: dict) -> Optional[Response]:
    if data is None:
        return None
    return Response(
        data['Message'] if 'Message' in data else '',
        data['Status'],
        data['Errcode'] if 'Errcode' in data else 0,
        data['Data']
    )


@dataclass
class Position:
    # 股票代码
    symbol_code: str
    # 股票名称
    symbol_name: str
    # 持仓数量
    hold_qty: int
    # 可用数量
    free_qty: int
    # 冻结数量
    frozen_qty: int
    # 成本价
    price: float
    # 当前最新价
    last_price: float
    # 盈亏率
    float_ratio: float
    # 浮动盈亏
    float_pnl: float
    # 最新市值
    last_market_value: float


def position_deserialize(data: dict) -> Position:
    ret = Position(
        data['Zqdm'].strip(),
        data['Zqmc'].strip(),
        get_int(data, 'Zqsl'),
        get_int(data, 'Kysl'),
        get_int(data, 'Djsl'),
        get_float(data, 'Cbjg'),
        get_float(data, 'Zxjg'),
        get_float(data, 'Ykbl'),
        get_float(data, 'Ljyk'),
        get_float(data, 'Zxsz')
    )
    return ret


@dataclass
class Asset:
    # 总资产
    total_asset: float
    # 总市值
    market_cap: float
    # 可用资金
    available_funds: float
    # 持仓盈亏
    position_pnl: float
    # 资金余额
    account_balance: float
    # 可取资金
    withdrawable_funds: float
    # 当日盈亏
    intraday_pnl: float
    # 冻结资金
    frozen_funds: float


@dataclass
class Account:
    # customer_code: str
    # shareholder_code: str
    asset: Asset
    positions: list[Position]


def account_deserialize(data: dict) -> Optional[Account]:
    pos = [position_deserialize(i) for i in data['positions']]
    return Account(
        Asset(
            get_float(data, 'Zzc'),
            get_float(data, 'Zxsz'),
            get_float(data, 'Kyzj'),
            get_float(data, 'Ljyk'),
            get_float(data, 'Zjye'),
            get_float(data, 'Kqzj'),
            get_float(data, 'Dryk'),
            get_float(data, 'Djzj')
        ),
        [i for i in pos if i.hold_qty > 0]
    )


@dataclass
class OrderInfo:
    symbol_code: str
    order_id: int
    insert_qty: int
    canceled_qty: int
    insert_price: float
    trade_price: float
    status: OrderStatus
    side: Direction

    # 报盘时间
    quotation_time: Optional[datetime.time]
    insert_time: Optional[datetime.datetime]
    _api: Optional[TradeApi] = None

    def is_alive(self) -> bool:
        return self.status == OrderStatus.PART_TRADED \
               or self.status == OrderStatus.INSERT_ACCEPTED \
               or self.status == OrderStatus.INSERT_SUBMITTED

    def cancel(self) -> bool:
        assert self._api is not None
        if not self.is_alive():
            return False

        code = self.insert_time.strftime('%Y%m%d') + '_' + str(self.order_id)
        return self._api.cancel_order(code)


def order_deserialize(data: dict) -> OrderInfo:
    return OrderInfo(
        symbol_code=data['Zqdm'],
        order_id=get_int(data, 'Wtbh'),
        insert_qty=get_int(data, 'Wtsl'),
        canceled_qty=get_int(data, 'Cdsl'),
        insert_price=get_float(data, 'Wtjg'),
        trade_price=get_float(data, 'Cjje'),
        status=order_status_parser(data['Wtzt'].strip()),
        side=Direction.Buy if data['Mmlb'] == 'B' else Direction.Sell,
        quotation_time=datetime.datetime.strptime(data['Bpsj'], '%H%M%S').time(),
        insert_time=datetime.datetime.strptime(data['Wtrq'] + data['Wtsj'], '%Y%m%d%H%M%S')
    )
