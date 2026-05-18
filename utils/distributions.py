"""随机分布函数"""
import numpy as np
import random
import config as cfg

def generate_demand():
    """正态需求，零截断"""
    d = int(np.random.normal(cfg.DEMAND_MEAN, cfg.DEMAND_STD))
    return max(0, d)

def generate_lead_time(mode='sea'):
    """物流提前期"""
    if mode == 'sea':
        lt = np.random.gamma(cfg.SEA_LT_SHAPE, cfg.SEA_LT_SCALE)
        return max(cfg.SEA_LT_MIN, int(round(lt)))
    else:
        lt = np.random.gamma(cfg.AIR_LT_SHAPE, cfg.AIR_LT_SCALE)
        return max(cfg.AIR_LT_MIN, int(round(lt)))

def generate_cash_delay(mbridge=False):
    """资金到账延迟"""
    if mbridge:
        return cfg.MBRIDGE_CASH_DELAY
    else:
        return random.randint(cfg.TRADITIONAL_CASH_DELAY_MIN,
                              cfg.TRADITIONAL_CASH_DELAY_MAX)

def set_seed():
    """固定随机种子"""
    np.random.seed(cfg.RANDOM_SEED)
    random.seed(cfg.RANDOM_SEED)