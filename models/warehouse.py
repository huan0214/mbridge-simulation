"""海外仓模型 - 唯一最终版本"""
import config as cfg
from utils.distributions import generate_demand, generate_lead_time, generate_cash_delay


class Warehouse:

    def __init__(self, s, S, transport_mode='sea', mbridge=False):
        self.s = s
        self.S = S
        self.transport_mode = transport_mode
        self.mbridge = mbridge

        # 状态变量
        self.inventory = cfg.INITIAL_INVENTORY
        self.in_transit = []  # [(数量, 剩余物流天数), ...]
        self.pending_orders = []  # [(数量, 剩余资金等待天数), ...]

        # 统计累计
        self.total_order_cost = 0
        self.total_hold_cost = 0
        self.total_stockout = 0
        self.num_orders = 0
        self.total_demand = 0

    def _receive_arrivals(self):
        """处理资金等待 → 物流在途"""
        still_pending = []
        for qty, wait_days in self.pending_orders:
            if wait_days <= 1:
                lt = generate_lead_time(self.transport_mode)
                self.in_transit.append([qty, lt])
            else:
                still_pending.append([qty, wait_days - 1])
        self.pending_orders = still_pending

    def _receive_logistics(self):
        """处理物流在途 → 可售库存"""
        arrived = 0
        still_in_transit = []
        for qty, days_left in self.in_transit:
            if days_left <= 1:
                arrived += qty
            else:
                still_in_transit.append([qty, days_left - 1])
        self.in_transit = still_in_transit
        self.inventory += arrived

    def _total_available(self):
        """计算总可用库存（在库 + 在途 + 待付款）"""
        return (self.inventory +
                sum(q for q, _ in self.in_transit) +
                sum(q for q, _ in self.pending_orders))

    def _check_reorder(self):
        """检查并触发补货"""
        if self._total_available() <= self.s:
            order_qty = self.S - self._total_available()
            cash_delay = generate_cash_delay(self.mbridge)

            if cash_delay == 0:
                lt = generate_lead_time(self.transport_mode)
                self.in_transit.append([order_qty, lt])
            else:
                self.pending_orders.append([order_qty, cash_delay])

            self.total_order_cost += cfg.FIXED_ORDER_COST
            self.num_orders += 1

    def step(self):
        """执行一天"""
        # 1. 资金到账 → 物流发出
        self._receive_arrivals()

        # 2. 物流到达 → 入库
        self._receive_logistics()

        # 3. 需求到达
        demand = generate_demand()
        self.total_demand += demand
        sold = min(self.inventory, demand)
        self.inventory -= sold
        self.total_stockout += (demand - sold)

        # 4. 补货决策
        self._check_reorder()

        # 5. 持有成本（含资金占用）
        capital_tied = sum(q for q, _ in self.pending_orders)
        self.total_hold_cost += (self.inventory + capital_tied) * cfg.HOLD_COST_PER_UNIT

    def run(self, days=None):
        """运行完整仿真"""
        if days is None:
            days = cfg.SIMULATION_DAYS
        for _ in range(1, days + 1):
            self.step()
        return self.get_results()

    def get_results(self):
        """返回结果字典"""
        total_cost = (self.total_order_cost +
                      self.total_hold_cost +
                      self.total_stockout * cfg.STOCKOUT_COST_PER_UNIT)
        service_level = (1 - self.total_stockout / self.total_demand
                         if self.total_demand > 0 else 0)

        return {
            'total_cost': total_cost,
            'service_level': service_level,
            'num_orders': self.num_orders,
            'total_stockout': self.total_stockout,
            'total_hold_cost': self.total_hold_cost,
            'total_order_cost': self.total_order_cost,
            'total_demand': self.total_demand
        }