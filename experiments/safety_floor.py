"""
最小安全库存下限：mBridge下物流随机性决定的安全库存底限
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import config as cfg
from utils.distributions import set_seed
import plotly.graph_objects as go


def run_safety_floor(days=365, n_runs=5,
                     demand_mean=10, demand_std=3,
                     stockout_cost=20, fixed_order_cost=50, hold_cost=0.5,
                     unit_cost_sea=2, unit_cost_air=8):
    K_values = [10, 25, 50, 100, 200]
    cv_values = [0.2, 0.4, 0.6, 0.8, 1.0]

    results = []

    print("=" * 60)
    print("  最小安全库存下限探索")
    print(f"  mBridge环境 | {days}天 × {n_runs}次重复")
    print("=" * 60)

    from app import SimulationWarehouse

    for K in K_values:
        for cv in cv_values:
            shape = max(1, int(1 / (cv ** 2)))
            scale = 7 / shape if cv < 0.5 else 30 / shape

            best_s = None
            best_cost = float('inf')

            for s in range(10, 120, 10):
                S = s + 40

                costs = []
                for _ in range(n_runs):
                    wh = SimulationWarehouse(
                        s=s, S=S, transport_mode='air', mbridge=True,
                        demand_mean=demand_mean, demand_std=demand_std,
                        stockout_cost=stockout_cost, fixed_order_cost=K,
                        hold_cost=hold_cost,
                        unit_cost_sea=unit_cost_sea, unit_cost_air=unit_cost_air
                    )
                    r = wh.run(days=days)
                    costs.append(r['total_cost'])

                avg_cost = np.mean(costs)
                if avg_cost < best_cost:
                    best_cost = avg_cost
                    best_s = s

            results.append({
                'K': K, 'cv': cv,
                'best_s': best_s,
                'best_cost': best_cost
            })

            print(f"  K={K:3d}, cv={cv:.1f} → 最优s={best_s:3d}, 成本={best_cost:.0f}元")

    return results


def plot_safety_floor(results):
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

    return fig