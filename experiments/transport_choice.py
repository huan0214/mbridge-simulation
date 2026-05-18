"""运输模式联合优化 V3：修复成本计算 + 平衡的运输模式选择"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import config as cfg
import numpy as np
import random
from utils.distributions import set_seed, generate_demand, generate_lead_time

class TransportChoiceWarehouse:
    """与Fixed模式完全可比：仅在补货时多一个运输模式选择"""

    def __init__(self, s, S, mbridge=False):
        self.s = s
        self.S = S
        self.mbridge = mbridge

        self.inventory = cfg.INITIAL_INVENTORY
        self.in_transit = []      # [qty, days_left, mode]
        self.pending_orders = []  # [qty, wait_days, mode]

        self.total_order_cost = 0    # K×次数(不含运输费，与fixed一致)
        self.total_hold_cost = 0
        self.total_stockout = 0
        self.num_orders = 0
        self.total_demand = 0

        self.sea_choices = 0
        self.air_choices = 0

        # 运输单价
        self.unit_cost_sea = cfg.SEA_UNIT_COST
        self.unit_cost_air = cfg.AIR_UNIT_COST

    def _choose_mode(self, order_qty):
        """
        决策规则：
        海运优势 = 运费低，劣势 = 周期长（持有成本高 + 缺货风险高）
        空运优势 = 周期短，劣势 = 运费高

        随着资金延迟消除(mBridge)，持有成本权重下降，
        空运的相对劣势（高运费）被周期短的优势进一步放大
        """
        # 期望提前期
        exp_lt_sea = cfg.SEA_LT_SHAPE * cfg.SEA_LT_SCALE
        exp_lt_air = cfg.AIR_LT_SHAPE * cfg.AIR_LT_SCALE

        # 持有成本权重：传统时资金成本高，mBridge时低
        weight = 1.5 if not self.mbridge else 0.5

        # 提前期差异带来的持有成本差异
        holding_diff = order_qty * cfg.HOLD_COST_PER_UNIT * (exp_lt_sea - exp_lt_air) * weight

        # 提前期标准差差异带来的风险
        std_sea = (cfg.SEA_LT_SHAPE * cfg.SEA_LT_SCALE**2) ** 0.5
        std_air = (cfg.AIR_LT_SHAPE * cfg.AIR_LT_SCALE**2) ** 0.5
        risk_sea = std_sea * cfg.DEMAND_MEAN * cfg.STOCKOUT_COST_PER_UNIT * 0.1
        risk_air = std_air * cfg.DEMAND_MEAN * cfg.STOCKOUT_COST_PER_UNIT * 0.1
        risk_diff = risk_sea - risk_air

        # 海运总劣势 = 额外持有成本 + 额外波动风险
        sea_disadvantage = holding_diff + risk_diff

        # 空运总劣势 = 额外运输费
        air_disadvantage = order_qty * (self.unit_cost_air - self.unit_cost_sea)

        # 选劣势更小的
        if air_disadvantage <= sea_disadvantage:
            return 'air'
        else:
            return 'sea'

    def _receive_arrivals(self):
        still_pending = []
        for item in self.pending_orders:
            qty, wait_days, mode = item
            if wait_days <= 1:
                lt = generate_lead_time(mode)
                self.in_transit.append([qty, lt, mode])
            else:
                still_pending.append([qty, wait_days - 1, mode])
        self.pending_orders = still_pending

    def _receive_logistics(self):
        arrived = 0
        still_in_transit = []
        for item in self.in_transit:
            qty, days_left, mode = item
            if days_left <= 1:
                arrived += qty
            else:
                still_in_transit.append([qty, days_left - 1, mode])
        self.in_transit = still_in_transit
        self.inventory += arrived

    def _total_available(self):
        return (self.inventory +
                sum(item[0] for item in self.in_transit) +
                sum(item[0] for item in self.pending_orders))

    def step(self):
        self._receive_arrivals()
        self._receive_logistics()

        demand = generate_demand()
        self.total_demand += demand
        sold = min(self.inventory, demand)
        self.inventory -= sold
        self.total_stockout += (demand - sold)

        total_avail = self._total_available()
        if total_avail <= self.s:
            order_qty = self.S - total_avail
            chosen_mode = self._choose_mode(order_qty)

            if chosen_mode == 'sea':
                self.sea_choices += 1
            else:
                self.air_choices += 1

            if self.mbridge:
                cash_delay = 0
            else:
                cash_delay = random.randint(1, 3)

            if cash_delay == 0:
                lt = generate_lead_time(chosen_mode)
                self.in_transit.append([order_qty, lt, chosen_mode])
            else:
                self.pending_orders.append([order_qty, cash_delay, chosen_mode])

            # 成本：K + 运输费
            transport_fee = order_qty * (self.unit_cost_sea if chosen_mode == 'sea' else self.unit_cost_air)
            self.total_order_cost += (cfg.FIXED_ORDER_COST + transport_fee)
            self.num_orders += 1

        capital_tied = sum(item[0] for item in self.pending_orders)
        self.total_hold_cost += (self.inventory + capital_tied) * cfg.HOLD_COST_PER_UNIT

    def run(self, days=None):
        if days is None:
            days = cfg.SIMULATION_DAYS
        for _ in range(1, days + 1):
            self.step()

        total_cost = (self.total_order_cost +
                      self.total_hold_cost +
                      self.total_stockout * cfg.STOCKOUT_COST_PER_UNIT)
        service_level = (1 - self.total_stockout / self.total_demand
                        if self.total_demand > 0 else 0)
        total_choices = self.sea_choices + self.air_choices
        air_pct = self.air_choices / total_choices * 100 if total_choices > 0 else 0

        return {
            'total_cost': total_cost, 'service_level': service_level,
            'num_orders': self.num_orders, 'total_stockout': self.total_stockout,
            'total_order_cost': self.total_order_cost,
            'total_hold_cost': self.total_hold_cost,
            'sea_choices': self.sea_choices, 'air_choices': self.air_choices,
            'air_pct': air_pct
        }


def run_repeated_joint(s, S, mbridge=False, days=365, n_runs=10):
    set_seed()
    costs, sls, orders, air_pcts = [], [], [], []
    for _ in range(n_runs):
        wh = TransportChoiceWarehouse(s=s, S=S, mbridge=mbridge)
        r = wh.run(days=days)
        costs.append(r['total_cost'])
        sls.append(r['service_level'])
        orders.append(r['num_orders'])
        air_pcts.append(r['air_pct'])
    return {
        'avg_cost': np.mean(costs), 'std_cost': np.std(costs),
        'avg_service': np.mean(sls), 'avg_orders': np.mean(orders),
        'avg_air_pct': np.mean(air_pcts)
    }


def run():
    from simulation.engine import run_repeated

    print("=" * 60)
    print("实验组3：运输模式联合优化 V3")
    print(f"策略: s=60, S=100 | 10次重复 | 365天")
    print("=" * 60)
    print()
    print("运输单价: 海运2元/件, 空运8元/件")
    print()

    s_opt, S_opt = 60, 100
    results = {}

    print("【固定模式对照组】")
    # 海运-传统
    print("  固定海运-传统 ...", end=" ", flush=True)
    r = run_repeated(s_opt, S_opt, 'sea', mbridge=False, n_runs=10)
    results['固定海运-传统'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}")

    # 海运-mBridge
    print("  固定海运-mBridge ...", end=" ", flush=True)
    r = run_repeated(s_opt, S_opt, 'sea', mbridge=True, n_runs=10)
    results['固定海运-mBridge'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}")

    # 空运-传统
    print("  固定空运-传统 ...", end=" ", flush=True)
    r = run_repeated(s_opt, S_opt, 'air', mbridge=False, n_runs=10)
    results['固定空运-传统'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}")

    # 空运-mBridge
    print("  固定空运-mBridge ...", end=" ", flush=True)
    r = run_repeated(s_opt, S_opt, 'air', mbridge=True, n_runs=10)
    results['固定空运-mBridge'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}")

    print()
    print("【联合优化实验组】")
    # 联合-传统
    print("  联合-传统 ...", end=" ", flush=True)
    r = run_repeated_joint(s_opt, S_opt, mbridge=False, n_runs=10)
    results['联合-传统'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}, 空运={r['avg_air_pct']:.0f}%")

    # 联合-mBridge
    print("  联合-mBridge ...", end=" ", flush=True)
    r = run_repeated_joint(s_opt, S_opt, mbridge=True, n_runs=10)
    results['联合-mBridge'] = r
    print(f"成本={r['avg_cost']:.0f}元, 服务={r['avg_service']:.1%}, 空运={r['avg_air_pct']:.0f}%")

    print()
    print("=" * 60)
    print("完整对比表")
    print("=" * 60)
    print(f"{'模型':<20s} {'成本':>8s} {'服务':>8s} {'空运占比':>8s}")
    print("-" * 50)

    for name in ['固定海运-传统', '固定海运-mBridge', '固定空运-传统', '固定空运-mBridge',
                  '联合-传统', '联合-mBridge']:
        r = results[name]
        if 'avg_air_pct' in r:
            air_str = f"{r['avg_air_pct']:.0f}%"
        elif '空运' in name and '海运' not in name:
            air_str = "100%"
        elif '海运' in name and '空运' not in name:
            air_str = "0%"
        else:
            air_str = "—"
        print(f"{name:<20s} {r['avg_cost']:>8.0f}元 {r['avg_service']:>7.1%} {air_str:>8s}")

    print()
    print("【论文核心发现】")

    # 发现1
    trad_air = results['固定空运-传统']['avg_cost']
    mbrg_air = results['固定空运-mBridge']['avg_cost']
    reduc = (trad_air - mbrg_air) / trad_air * 100
    print(f"1. 空运mBridge降本: {reduc:.1f}% ({trad_air:.0f}→{mbrg_air:.0f}元)")

    # 发现2
    trad_pct = results['联合-传统']['avg_air_pct']
    mbrg_pct = results['联合-mBridge']['avg_air_pct']
    print(f"2. 运输模式选择: 传统空运{trad_pct:.0f}% → mBridge空运{mbrg_pct:.0f}%")

    # 发现3
    sea_cost = results['固定海运-mBridge']['avg_cost']
    air_cost = results['固定空运-mBridge']['avg_cost']
    best = '空运' if air_cost < sea_cost else '海运'
    print(f"3. mBridge最优固定模式: {best} (海运{sea_cost:.0f} vs 空运{air_cost:.0f}元)")

    # 发现4：公平对比
    fixed_orders = results['固定空运-mBridge']['avg_orders']
    avg_qty = S_opt - s_opt  # 40件
    fixed_transport = fixed_orders * avg_qty * 8
    fixed_total = results['固定空运-mBridge']['avg_cost'] + fixed_transport
    joint_total = results['联合-mBridge']['avg_cost']

    print(f"4. 公平对比(均含运输费):")
    print(f"   固定空运: {results['固定空运-mBridge']['avg_cost']:.0f} + 运输费{fixed_transport:.0f} = {fixed_total:.0f}元")
    print(f"   联合优化: {joint_total:.0f}元")
    if joint_total <= fixed_total:
        print(f"   ✓ 联合优化优于固定空运")
    else:
        print(f"   差异: {joint_total - fixed_total:.0f}元 (联合优化考虑了运输模式选择成本)")


if __name__ == '__main__':
    run()