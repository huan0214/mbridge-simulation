"""
资金效率相图：系统性地改变资金到账时间
找到策略从"海运主导"突变为"空运主导"的临界点
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import random
import config as cfg
from utils.distributions import set_seed
import plotly.graph_objects as go


def run_phase_diagram(s=60, S=100, days=365, n_runs=5,
                      demand_mean=10, demand_std=3,
                      stockout_cost=20, fixed_order_cost=50, hold_cost=0.5,
                      unit_cost_sea=2, unit_cost_air=8):
    """
    资金延迟从0到3天，分多档测试
    """
    delays_hours = [0, 1, 3, 6, 12, 24, 48, 72]
    delay_labels = ['0(秒级)', '1小时', '3小时', '6小时', '12小时', '1天', '2天', '3天']

    results = {'delay_hours': [], 'delay_labels': [],
               'sea_cost': [], 'air_cost': [],
               'sea_service': [], 'air_service': [],
               'best_mode': [], 'cost_saving': []}

    print("=" * 60)
    print("  资金效率相图：寻找策略突变临界点")
    print(f"  策略 s={s}, S={S} | {days}天 × {n_runs}次重复")
    print("=" * 60)
    print()

    from app import SimulationWarehouse

    for dh, dl in zip(delays_hours, delay_labels):
        print(f"资金延迟: {dl:>8s} ...", end=" ", flush=True)

        delay_days = dh / 24.0

        sea_costs, sea_sls = [], []
        air_costs, air_sls = [], []

        for _ in range(n_runs):
            wh_sea = SimulationWarehouse(
                s=s, S=S, transport_mode='sea', mbridge=(dh==0),
                demand_mean=demand_mean, demand_std=demand_std,
                stockout_cost=stockout_cost, fixed_order_cost=fixed_order_cost,
                hold_cost=hold_cost,
                unit_cost_sea=unit_cost_sea, unit_cost_air=unit_cost_air,
                cash_delay_days=(delay_days if dh > 0 else None)
            )

            wh_air = SimulationWarehouse(
                s=s, S=S, transport_mode='air', mbridge=(dh==0),
                demand_mean=demand_mean, demand_std=demand_std,
                stockout_cost=stockout_cost, fixed_order_cost=fixed_order_cost,
                hold_cost=hold_cost,
                unit_cost_sea=unit_cost_sea, unit_cost_air=unit_cost_air,
                cash_delay_days=(delay_days if dh > 0 else None)
            )

            r_sea = wh_sea.run(days=days)
            r_air = wh_air.run(days=days)

            sea_costs.append(r_sea['total_cost'])
            sea_sls.append(r_sea['service_level'])
            air_costs.append(r_air['total_cost'])
            air_sls.append(r_air['service_level'])

        avg_sea_cost = np.mean(sea_costs)
        avg_air_cost = np.mean(air_costs)
        avg_sea_sl = np.mean(sea_sls)
        avg_air_sl = np.mean(air_sls)

        best = '空运' if avg_air_cost < avg_sea_cost else '海运'
        saving = (avg_sea_cost - avg_air_cost) / avg_sea_cost * 100 if avg_sea_cost > avg_air_cost else 0

        results['delay_hours'].append(dh)
        results['delay_labels'].append(dl)
        results['sea_cost'].append(avg_sea_cost)
        results['air_cost'].append(avg_air_cost)
        results['sea_service'].append(avg_sea_sl)
        results['air_service'].append(avg_air_sl)
        results['best_mode'].append(best)
        results['cost_saving'].append(saving)

        print(f"海运={avg_sea_cost:.0f}元({avg_sea_sl:.1%}) | "
              f"空运={avg_air_cost:.0f}元({avg_air_sl:.1%}) | "
              f"最优={best}")

    return results


def plot_phase_diagram(results):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=results['delay_labels'], y=results['sea_cost'],
        mode='lines+markers', name='海运成本',
        line=dict(color='#3498db', width=3), marker=dict(size=10)
    ))
    fig.add_trace(go.Scatter(
        x=results['delay_labels'], y=results['air_cost'],
        mode='lines+markers', name='空运成本',
        line=dict(color='#2ecc71', width=3), marker=dict(size=10)
    ))

    for i, (label, mode) in enumerate(zip(results['delay_labels'], results['best_mode'])):
        y_pos = max(results['sea_cost'][i], results['air_cost'][i]) * 1.05
        color = '#2ecc71' if mode == '空运' else '#3498db'
        fig.add_annotation(x=label, y=y_pos, text=f'最优:{mode}',
                          showarrow=False, font=dict(color=color, size=11, weight='bold'))

    fig.update_layout(
        title='<b>资金效率相图：最优运输模式随资金延迟的变化</b>',
        xaxis_title='资金到账延迟时间',
        yaxis_title='年总成本（元）',
        height=500,
        hovermode='x unified'
    )

    return fig