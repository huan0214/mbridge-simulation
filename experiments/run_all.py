"""运行四组完整对比实验"""
import config as cfg
from simulation.engine import run_repeated
from utils.distributions import set_seed


def run_all_experiments(s, S, days=None, n_runs=None):
    """返回: dict {组名: {avg_cost, std_cost, ...}}"""
    set_seed()

    if days is None:
        days = cfg.SIMULATION_DAYS
    if n_runs is None:
        n_runs = cfg.N_REPETITIONS

    configs = [
        ("传统-海运", "sea", False, s, S),
        ("传统-空运", "air", False, s, S),
        ("mBridge-海运", "sea", True, s, S),
        ("mBridge-空运", "air", True, s, S),
    ]

    results = {}
    for name, mode, mbridge, s_val, S_val in configs:
        print(f"运行: {name} ...", end=" ", flush=True)
        results[name] = run_repeated(s_val, S_val, mode, mbridge, days, n_runs)
        r = results[name]
        print(f"成本={r['avg_cost']:.0f}±{r['std_cost']:.0f}, "
              f"服务={r['avg_service']:.1%}, 订货={r['avg_orders']:.1f}次")

    return results


def print_report(results):
    """打印结果报告"""
    print(f"\n{'=' * 60}")
    print(f"{'组别':<20s} {'成本':>10s} {'服务':>8s} {'订货/年':>8s} {'缺货':>6s}")
    print("-" * 55)
    for name, r in results.items():
        print(f"{name:<20s} {r['avg_cost']:>8.0f}元 {r['avg_service']:>7.1%} "
              f"{r['avg_orders']:>6.1f}次 {r['avg_stockout']:>4.0f}件")

    print(f"\n{'=' * 60}")
    print("mBridge 效果: 传统 → mBridge")
    print(f"{'=' * 60}")

    for mode_label in ["海运", "空运"]:
        trad = results[f"传统-{mode_label}"]
        mbrg = results[f"mBridge-{mode_label}"]
        cost_change = (mbrg['avg_cost'] - trad['avg_cost']) / trad['avg_cost'] * 100
        sl_change = (mbrg['avg_service'] - trad['avg_service']) * 100

        print(f"\n【{mode_label}】")
        print(f"  成本: {cost_change:+.1f}% ({trad['avg_cost']:.0f} → {mbrg['avg_cost']:.0f}元)")
        print(f"  服务: {sl_change:+.1f}百分点 ({trad['avg_service']:.1%} → {mbrg['avg_service']:.1%})")
        print(f"  订货: {trad['avg_orders']:.1f} → {mbrg['avg_orders']:.1f}次/年")