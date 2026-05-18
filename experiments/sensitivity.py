"""敏感性分析：改变缺货惩罚 π，看结论是否稳健"""
import sys
import os

sys.path.append(os.path.dirname(__file__))

import config as cfg
from simulation.engine import run_repeated
from utils.distributions import set_seed
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def run_sensitivity(pi_values, s=60, S=100, days=365, n_runs=20):
    """
    对不同的π值，分别跑传统和mBridge
    返回: {pi: {传统成本, mBridge成本, 传统服务, mBridge服务}}
    """
    set_seed()
    results = {}

    original_pi = cfg.STOCKOUT_COST_PER_UNIT

    for pi in pi_values:
        # 临时修改缺货成本
        cfg.STOCKOUT_COST_PER_UNIT = pi

        print(f"  π={pi:3d}元/件 ...", end=" ", flush=True)

        trad_sea = run_repeated(s, S, 'sea', mbridge=False, days=days, n_runs=n_runs)
        mbrg_sea = run_repeated(s, S, 'sea', mbridge=True, days=days, n_runs=n_runs)
        trad_air = run_repeated(s, S, 'air', mbridge=False, days=days, n_runs=n_runs)
        mbrg_air = run_repeated(s, S, 'air', mbridge=True, days=days, n_runs=n_runs)

        results[pi] = {
            '传统-海运': trad_sea, 'mBridge-海运': mbrg_sea,
            '传统-空运': trad_air, 'mBridge-空运': mbrg_air,
        }
        print("完成")

    # 恢复原值
    cfg.STOCKOUT_COST_PER_UNIT = original_pi
    return results


def plot_sensitivity(results, save_path=None):
    """画敏感性分析图：不同π下的成本和优势"""
    pi_values = sorted(results.keys())

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # === 左图：成本变化 ===
    ax = axes[0]
    x = range(len(pi_values))
    width = 0.35

    trad_costs = [results[pi]['传统-空运']['avg_cost'] for pi in pi_values]
    mbrg_costs = [results[pi]['mBridge-空运']['avg_cost'] for pi in pi_values]

    ax.bar([i - width / 2 for i in x], trad_costs, width, color='#3498db',
           edgecolor='black', linewidth=0.5, label='传统 (SWIFT)')
    ax.bar([i + width / 2 for i in x], mbrg_costs, width, color='#2ecc71',
           edgecolor='black', linewidth=0.5, label='mBridge')

    ax.set_xticks(x)
    ax.set_xticklabels([f'π={p}' for p in pi_values], fontsize=11)
    ax.set_ylabel('年总成本 (元)', fontsize=12)
    ax.set_title('空运：不同缺货惩罚下的成本对比', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # === 右图：mBridge成本降幅 ===
    ax = axes[1]
    reductions = []
    for pi in pi_values:
        trad = results[pi]['传统-空运']['avg_cost']
        mbrg = results[pi]['mBridge-空运']['avg_cost']
        reductions.append((trad - mbrg) / trad * 100)

    ax.plot(pi_values, reductions, 'o-', color='#2ecc71', linewidth=2, markersize=10)
    ax.set_xlabel('缺货惩罚 π (元/件)', fontsize=12)
    ax.set_ylabel('mBridge成本降幅 (%)', fontsize=12)
    ax.set_title('mBridge优势随π的变化', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3, linestyle='--')

    # 标注数值
    for pi, red in zip(pi_values, reductions):
        ax.annotate(f'{red:.1f}%', (pi, red), textcoords="offset points",
                    xytext=(0, 12), ha='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")
    plt.show()


def run():
    """运行敏感性分析"""
    n_runs = 20  # ← 先定义
    pi_values = [5, 10, 20, 30, 50]

    print("=" * 60)
    print("敏感性分析：缺货惩罚 π 的影响")
    print(f"策略: s=60, S=100 | 重复{n_runs}次 | 365天")  # ← 再使用
    print("=" * 60)

    results = run_sensitivity(pi_values, n_runs=n_runs)

    # 打印表格
    print(f"\n{'=' * 70}")
    print(
        f"{'π':<6s} {'传统-海运':>10s} {'mBridge-海运':>10s} {'传统-空运':>10s} {'mBridge-空运':>10s} {'空运降幅':>8s}")
    print("-" * 65)
    for pi in pi_values:
        t_sea = results[pi]['传统-海运']['avg_cost']
        m_sea = results[pi]['mBridge-海运']['avg_cost']
        t_air = results[pi]['传统-空运']['avg_cost']
        m_air = results[pi]['mBridge-空运']['avg_cost']
        reduction = (t_air - m_air) / t_air * 100
        print(f"π={pi:<3d}  {t_sea:>8.0f}元  {m_sea:>8.0f}元  {t_air:>8.0f}元  {m_air:>8.0f}元  {reduction:>6.1f}%")

    print(f"\n结论: ", end="")
    reductions = [(results[pi]['传统-空运']['avg_cost'] - results[pi]['mBridge-空运']['avg_cost'])
                  / results[pi]['传统-空运']['avg_cost'] * 100 for pi in pi_values]
    if all(r > 0 for r in reductions):
        print("在所有π值下，mBridge空运成本均低于传统模型，结论稳健 ✓")
    else:
        print("注意：部分π值下结论反转，需进一步分析")

    # 画图
    plot_sensitivity(results, save_path='sensitivity_pi.png')


if __name__ == '__main__':
    run()