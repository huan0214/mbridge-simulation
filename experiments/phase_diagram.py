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
from models.warehouse import Warehouse
from utils.distributions import set_seed
import plotly.graph_objects as go


def run_phase_diagram(s=60, S=100, days=365, n_runs=10):
    """
    资金延迟从0到3天，分多档测试
    返回每个延迟下的空运/海运成本、服务水平和策略选择
    """
    # 资金延迟梯度（小时），0=秒级mBridge
    delays_hours = [0, 1, 3, 6, 12, 24, 48, 72]  # 0h, 1h, 3h, 6h, 12h, 1天, 2天, 3天
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

    for dh, dl in zip(delays_hours, delay_labels):
        print(f"资金延迟: {dl:>8s} ...", end=" ", flush=True)

        # 临时修改资金延迟参数（小时转天）
        delay_days = dh / 24.0

        # 跑海运
        sea_costs, sea_sls = [], []
        air_costs, air_sls = [], []

        for _ in range(n_runs):
            # 海运
            wh_sea = Warehouse(s=s, S=S, transport_mode='sea', mbridge=(dh == 0))
            if dh > 0:
                # 修改传统延迟范围
                wh_sea._cash_delay = delay_days
            else:
                wh_sea.mbridge = True

            # 空运
            wh_air = Warehouse(s=s, S=S, transport_mode='air', mbridge=(dh == 0))
            if dh > 0:
                wh_air._cash_delay = delay_days
            else:
                wh_air.mbridge = True

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
    """画相图"""
    fig = go.Figure()

    # 两条成本线
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

    # 标注最优模式
    for i, (label, mode) in enumerate(zip(results['delay_labels'], results['best_mode'])):
        y_pos = max(results['sea_cost'][i], results['air_cost'][i]) + 2000
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


if __name__ == '__main__':
    results = run_phase_diagram(s=60, S=100, days=365, n_runs=5)

    print(f"\n{'=' * 60}")
    print("  相图结论")
    print(f"{'=' * 60}")
    print(f"  资金延迟梯度: {results['delay_labels']}")
    print(f"  各延迟下的最优模式: {results['best_mode']}")

    fig = plot_phase_diagram(results)
    fig.show()