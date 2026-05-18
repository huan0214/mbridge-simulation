"""
最小安全库存下限：mBridge下物流随机性决定的安全库存底限
找到K、σL与最小安全库存s的关系
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import config as cfg
from models.warehouse import Warehouse
from utils.distributions import set_seed
import plotly.graph_objects as go


def run_safety_floor(days=365, n_runs=5):
    """
    在mBridge环境下，改变固定订货费K和提前期标准差
    观察最优安全库存s的变化
    """
    # K值梯度
    K_values = [10, 25, 50, 100, 200]
    # 提前期变异系数（标准差/均值）
    cv_values = [0.2, 0.4, 0.6, 0.8, 1.0]  # 0.2=稳定空运, 1.0=极不稳定海运

    results = []

    print("=" * 60)
    print("  最小安全库存下限探索")
    print(f"  mBridge环境 | {days}天 × {n_runs}次重复")
    print("=" * 60)

    for K in K_values:
        for cv in cv_values:
            # 构建对应cv的Gamma参数
            # cv = std/mean = sqrt(shape*scale^2)/(shape*scale) = 1/sqrt(shape)
            shape = int(1 / (cv ** 2))
            scale = 7 / shape if cv < 0.5 else 30 / shape  # 均值7天(快)或30天(慢)

            # 临时修改
            old_K = cfg.FIXED_ORDER_COST
            cfg.FIXED_ORDER_COST = K

            # 找到这个K和cv下的最优s（用网格搜索）
            best_s = None
            best_cost = float('inf')

            for s in range(10, 120, 10):
                S = s + 40  # 固定S-s=40

                costs = []
                for _ in range(n_runs):
                    wh = Warehouse(s=s, S=S, transport_mode='air', mbridge=True)
                    r = wh.run(days=days)
                    costs.append(r['total_cost'])

                avg_cost = np.mean(costs)
                if avg_cost < best_cost:
                    best_cost = avg_cost
                    best_s = s

            results.append({
                'K': K, 'cv': cv,
                'best_s': best_s,
                'best_cost': best_cost,
                'shape': shape, 'scale': scale
            })

            print(f"  K={K:3d}, cv={cv:.1f} → 最优s={best_s:3d}, 成本={best_cost:.0f}元")

            cfg.FIXED_ORDER_COST = old_K

    return results


def plot_safety_floor(results):
    """画最小安全库存热力图"""
    K_values = sorted(set(r['K'] for r in results))
    cv_values = sorted(set(r['cv'] for r in results))

    z_data = []
    for cv in cv_values:
        row = []
        for K in K_values:
            for r in results:
                if r['K'] == K and r['cv'] == cv:
                    row.append(r['best_s'])
                    break
        z_data.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[f'K={k}' for k in K_values],
        y=[f'cv={cv}' for cv in cv_values],
        colorscale='RdYlGn_r',
        text=[[f's={val}' for val in row] for row in z_data],
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title='最优s值')
    ))

    fig.update_layout(
        title='<b>最小安全库存下限热力图</b><br><sub>mBridge环境下，K与σL对最优再订货点s的影响</sub>',
        xaxis_title='固定订货费 K（元/次）',
        yaxis_title='提前期变异系数 cv（σ/μ）',
        height=500
    )

    # 经验公式注解
    fig.add_annotation(
        x=2, y=4.5,
        text='s ∝ √(K × cv × D̄)<br>D̄=日均需求',
        showarrow=False,
        font=dict(size=13, color='darkblue'),
        bgcolor='rgba(255,255,255,0.8)'
    )

    return fig


if __name__ == '__main__':
    results = run_safety_floor(days=365, n_runs=5)
    fig = plot_safety_floor(results)
    fig.show()