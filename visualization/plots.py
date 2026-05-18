"""可视化 - 最终版"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

# ===== 字体配置 =====
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def plot_cost_comparison(results, save_path=None):
    """四组成本对比柱状图"""
    names = ["传统-海运", "mBridge-海运", "传统-空运", "mBridge-空运"]
    costs = [results[n]['avg_cost'] for n in names]
    errors = [results[n]['std_cost'] for n in names]

    colors = ['#3498db', '#2ecc71', '#3498db', '#2ecc71']

    fig, ax = plt.subplots(figsize=(12, 7))
    x_pos = range(len(names))
    bars = ax.bar(x_pos, costs, color=colors, edgecolor='black', linewidth=0.8)

    # 数值标签（放在柱上方，留间距）
    for i, (bar, cost) in enumerate(zip(bars, costs)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1500,
                f'{cost:,.0f}元', ha='center', va='bottom', fontsize=13, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, fontsize=12)
    ax.set_ylabel('年总成本 (元)', fontsize=14)
    ax.set_title('mBridge vs 传统模型：年总成本对比', fontsize=16, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 让y轴上限留出标签空间
    ax.set_ylim(0, max(costs) * 1.2)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#3498db', label='传统 (SWIFT, T+1~3天)'),
        Patch(facecolor='#2ecc71', label='mBridge (T+6~9秒)')
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='upper right')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")
    plt.show()


def plot_service_level(results, save_path=None):
    """服务水平对比"""
    names = ["传统-海运", "mBridge-海运", "传统-空运", "mBridge-空运"]
    service = [results[n]['avg_service'] * 100 for n in names]

    colors = ['#3498db', '#2ecc71', '#3498db', '#2ecc71']

    fig, ax = plt.subplots(figsize=(12, 7))
    x_pos = range(len(names))
    bars = ax.bar(x_pos, service, color=colors, edgecolor='black', linewidth=0.8)

    for bar, sl in zip(bars, service):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{sl:.1f}%', ha='center', va='bottom', fontsize=13, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, fontsize=12)
    ax.set_ylabel('服务水平 (%)', fontsize=14)
    ax.set_title('mBridge vs 传统模型：服务水平对比', fontsize=16, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 105)

    # 画一条90%参考线
    ax.axhline(y=90, color='red', linestyle='--', linewidth=1, alpha=0.6)
    ax.text(3.5, 91, '90%目标线', color='red', fontsize=10, ha='right')

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#3498db', label='传统 (SWIFT, T+1~3天)'),
        Patch(facecolor='#2ecc71', label='mBridge (T+6~9秒)')
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='lower right')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"  图表已保存: {save_path}")
    plt.show()