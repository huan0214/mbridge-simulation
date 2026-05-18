"""
所有可调参数集中在这里
修改一处，全局生效
"""

# ===== 成本参数 =====
FIXED_ORDER_COST = 50       # K: 每次订货固定成本
HOLD_COST_PER_UNIT = 0.5    # h: 每件每天持有成本
STOCKOUT_COST_PER_UNIT = 20 # π: 每件缺货惩罚

# ===== 需求参数 =====
DEMAND_MEAN = 10            # 日均需求均值
DEMAND_STD = 3              # 日均需求标准差

# ===== 物流参数 =====
# 海运: Gamma分布
SEA_LT_SHAPE = 5
SEA_LT_SCALE = 6            # 均值 = shape * scale = 30天
SEA_LT_MIN = 3

# 空运: Gamma分布
AIR_LT_SHAPE = 5
AIR_LT_SCALE = 1.4          # 均值 = 7天
AIR_LT_MIN = 3

# ===== 资金延迟参数 =====
TRADITIONAL_CASH_DELAY_MIN = 1   # 传统模型: T+1
TRADITIONAL_CASH_DELAY_MAX = 3   # 传统模型: T+3
MBRIDGE_CASH_DELAY = 0           # mBridge: 0天

# ===== 仿真参数 =====
SIMULATION_DAYS = 365       # 仿真天数
N_REPETITIONS = 30          # 重复次数
INITIAL_INVENTORY = 50      # 初始库存

# ===== 网格搜索参数 =====
S_MIN = 5
S_MAX = 60
S_STEP = 5
S_DELTA_MIN = 10            # S - s 的最小值
S_DELTA_MAX = 50            # S - s 的最大值
S_DELTA_STEP = 10

# ===== 随机种子（可复现） =====
RANDOM_SEED = 42
# ===== 运输成本参数 =====
SEA_UNIT_COST = 2       # 海运每件运费
AIR_UNIT_COST = 8       # 空运每件运费