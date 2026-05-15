import numpy as np
import matplotlib.pyplot as plt


def plot_functions(param_sets, x_min=0.01, x_max=10, num_points=1000):
    """
    批量绘制函数：y = b/(dop^a) + c*(dop^d) + e

    参数：
        param_sets : 参数列表，每个元素是一个 dict，示例：
            {
                "name": "case1",   # 图例名称（可选）
                "a": 1.5,
                "b": 10,
                "c": 0.5,
                "d": 2,
                "e": 1,
            }
        x_min, x_max : dop 的绘图范围
        num_points   : 曲线点数
    """
    dop = np.linspace(x_min, x_max, num_points)

    plt.figure(figsize=(8, 6))
    for i, p in enumerate(param_sets, start=1):
        a = p["a"]
        b = p["b"]
        c = p["c"]
        d = p["d"]
        e = p["e"]
        name = p.get("name", f"case{i}")

        y = b / (dop ** a) + c * (dop ** d) + e
        label = f'{name}: y = {b}/dop^{a} + {c}·dop^{d} + {e}'
        plt.plot(dop, y, linewidth=2, label=label)

    plt.xlabel('dop', fontsize=12)
    plt.ylabel('y', fontsize=12)
    plt.title('Function curves', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.show()


# ========== 在这里配置多组参数（可增删） ==========
PARAM_SETS = [
    # {
    #     "name": "tablescan",
    #     "a": 0.0,
    #     "b": 216.86057,
    #     "c": 90.97139,
    #     "d": 0.10308,
    #     "e": 133.80511
    # },
    # {
    #     "name": "tablescan",
    #     "a": 2.0,
    #     "b": 0.000001,
    #     "c": 3143902000.0,
    #     "d": 0,
    #     "e": 4216404700.0
    # },
    {
        "name": "tablescan",
        "a": 1.105,
        "b": 30369,
        "c": -0.2279,
        "d": 0.53,
        "e":-0.08 
    }
]
# =================================================

plot_functions(PARAM_SETS, x_min=8, x_max=160)
