"""仿真引擎：重复运行 + 统计"""
import numpy as np
from models.warehouse import Warehouse
from utils.distributions import set_seed


def run_repeated(s, S, mode='sea', mbridge=False, days=None, n_runs=None):
    """
    重复运行n次取平均
    返回: {avg_cost, std_cost, avg_service, avg_orders, avg_stockout}
    """
    import config as cfg
    if days is None:
        days = cfg.SIMULATION_DAYS
    if n_runs is None:
        n_runs = cfg.N_REPETITIONS

    set_seed()  # 每次调用重置种子，保证可复现

    costs, sls, orders, stockouts = [], [], [], []

    for _ in range(n_runs):
        wh = Warehouse(s=s, S=S, transport_mode=mode, mbridge=mbridge)
        r = wh.run(days=days)
        costs.append(r['total_cost'])
        sls.append(r['service_level'])
        orders.append(r['num_orders'])
        stockouts.append(r['total_stockout'])

    return {
        'avg_cost': np.mean(costs),
        'std_cost': np.std(costs),
        'avg_service': np.mean(sls),
        'avg_orders': np.mean(orders),
        'avg_stockout': np.mean(stockouts)
    }