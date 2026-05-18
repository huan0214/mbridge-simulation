"""网格搜索最优(s, S)"""
import config as cfg
from models.warehouse import Warehouse
from utils.distributions import set_seed


def grid_search(mode='sea', mbridge=True, days=None):
    """返回: best_s, best_S, best_cost, best_sl, all_results"""
    if days is None:
        days = cfg.SIMULATION_DAYS

    set_seed()

    best_cost = float('inf')
    best_s = best_S = best_sl = None
    all_results = []

    for s in range(cfg.S_MIN, cfg.S_MAX + 1, cfg.S_STEP):
        for delta in range(cfg.S_DELTA_MIN, cfg.S_DELTA_MAX + 1, cfg.S_DELTA_STEP):
            S = s + delta
            wh = Warehouse(s=s, S=S, transport_mode=mode, mbridge=mbridge)
            r = wh.run(days=days)

            all_results.append((s, S, r['total_cost'], r['service_level']))

            if r['total_cost'] < best_cost:
                best_cost = r['total_cost']
                best_s = s
                best_S = S
                best_sl = r['service_level']

    return best_s, best_S, best_cost, best_sl, all_results