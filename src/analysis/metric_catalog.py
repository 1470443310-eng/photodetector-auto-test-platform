"""Chinese teaching labels and plain-language interpretations for metrics."""
from __future__ import annotations

STATUS_NAMES = {
    "PASS": "通过（PASS）", "FAIL": "不合格（FAIL）", "ERROR": "测试异常（ERROR）",
}

PROFILE_NAMES = {
    "normal": "正常器件", "high_dark_current": "暗电流偏大", "low_responsivity": "响应度偏低",
    "noisy": "噪声/接触不稳定", "nonlinear": "光响应非线性", "open_circuit": "开路",
    "short_circuit": "短路", "communication_error": "仪器通信异常", "unstable": "长期漂移",
    "spectral_mismatch": "光谱峰值偏移",
}

METRIC_CATALOG = {
    "dark_current_a": ("暗电流", "A", "没有光照时仍流过的电流；越小通常越容易检测弱光。", "检查遮光、温度、表面污染、线缆漏电和器件损伤。"),
    "responsivity_a_per_w": ("响应度", "A/W", "每1 W入射光能产生多少光电流；过低表示光电转换能力不足。", "检查波长是否匹配、光功率校准、光路对准和器件老化。"),
    "noise_rms_a": ("暗噪声RMS", "A", "暗态电流的波动大小；噪声越大，微弱信号越容易被淹没。", "检查屏蔽接地、带宽、积分时间、环境光和接触稳定性。"),
    "nep_w_per_sqrt_hz": ("噪声等效功率 NEP", "W/√Hz", "产生与噪声相同信号所需的最小光功率；越小越好。", "先排查噪声和响应度，因为 NEP 同时受两者影响。"),
    "detectivity_jones": ("比探测率 D*", "Jones", "综合面积和NEP后比较弱光探测能力；同类器件中越大越好。", "检查NEP、有效面积、温度和带宽口径是否一致。"),
    "linearity_r_squared": ("线性拟合 R²", "", "光功率变化时输出是否接近直线；越接近1越好。", "检查是否饱和、功率计量程、负载和光源稳定性。"),
    "linearity_max_error_fraction": ("线性最大偏差", "%FS", "相对满量程的最大偏离；越小越好。", "降低光功率或偏压，并检查放大器、Compliance和器件饱和。"),
    "repeatability_cv": ("重复性 CV", "%", "相同条件重复测量的一致程度；越小表示短期重复性越好。", "检查夹具接触、等待时间、环境扰动和仪器量程。"),
    "stability_drift_fraction": ("稳定性漂移", "%", "一段时间内首尾结果的变化；越小表示更稳定。", "检查温度预热、光源漂移、机械位移和器件老化。"),
    "target_spectral_ratio": ("目标波长相对响应", "%峰值", "目标波长响应占峰值响应的比例；过低说明波长不匹配。", "检查光源波长、滤光片和器件材料/型号是否匹配。"),
    "spectral_peak_wavelength_nm": ("光谱峰值波长", "nm", "器件最敏感的波长位置，用于判断光源与探测器是否匹配。", "与数据手册和光源中心波长对照。"),
    "estimated_shunt_resistance_ohm": ("估算并联电阻", "Ω", "由暗态I–V斜率估算的漏电通道电阻；通常越大漏电越小。", "检查暗态I–V斜率、治具绝缘和表面清洁。"),
}

FAILURE_EXPLANATIONS = {
    "电流达到保护限值": "电流触发仪器 Compliance，可能是短路、接线错误或偏压过高。",
    "暗电流超过上限": "暗态漏电过大，会压缩弱光检测范围。",
    "响应度低于下限": "同样光功率产生的信号偏小。",
    "响应度高于上限": "结果异常偏高，可能有光功率标定、增益或杂散光问题。",
    "重复性CV超过上限": "同样条件多次测量离散过大。",
    "暗噪声RMS超过上限": "暗态波动过大，弱光信号可能被噪声淹没。",
    "NEP超过上限": "需要更强的光才能超过噪声，弱光检测能力不足。",
    "比探测率D*低于下限": "按面积归一化后的探测能力不足。",
    "线性拟合R²低于下限": "输出与光功率不再保持良好直线关系。",
    "线性最大偏差超过上限": "至少一个功率点明显偏离理想直线。",
    "稳定性漂移超过上限": "测量随时间发生明显漂移。",
    "稳定性极差超过上限": "时间序列最大最小差距过大。",
    "目标波长相对响应低于下限": "器件在目标光源波长处不够敏感。",
    "数据清洗剔除了无效测量点": "原始采集含NaN或无穷值，需要检查仪器和数据传输。",
}


def metric_guide_rows() -> list[dict[str, str]]:
    return [{"指标": item[0], "单位": item[1], "通俗解释": item[2], "失败后优先检查": item[3]} for item in METRIC_CATALOG.values()]


def display_metric_name(key: str) -> str:
    return METRIC_CATALOG.get(key, (key, "", "", ""))[0]


def metric_assessment(key: str, value: float, limits: dict) -> tuple[str, str]:
    rules = {
        "dark_current_a": (None, limits.get("dark_current_max_a")),
        "responsivity_a_per_w": (limits.get("responsivity_min_a_per_w"), limits.get("responsivity_max_a_per_w")),
        "noise_rms_a": (None, limits.get("noise_rms_max_a")),
        "nep_w_per_sqrt_hz": (None, limits.get("nep_max_w_per_sqrt_hz")),
        "detectivity_jones": (limits.get("detectivity_min_jones"), None),
        "linearity_r_squared": (limits.get("linearity_r_squared_min"), None),
        "linearity_max_error_fraction": (None, limits.get("linearity_max_error_fraction")),
        "repeatability_cv": (None, limits.get("repeatability_cv_max")),
        "stability_drift_fraction": (None, limits.get("stability_drift_max_fraction")),
        "target_spectral_ratio": (limits.get("target_spectral_ratio_min"), None),
    }
    if key not in rules:
        return "观察项", "无独立判定阈值"
    lower, upper = rules[key]
    passed = (lower is None or value >= float(lower)) and (upper is None or value <= float(upper))
    if lower is not None and upper is not None:
        specification = f"{float(lower):.3e} ～ {float(upper):.3e}"
    elif lower is not None:
        specification = f"≥ {float(lower):.3e}"
    else:
        specification = f"≤ {float(upper):.3e}"
    return ("合格" if passed else "不合格"), specification
