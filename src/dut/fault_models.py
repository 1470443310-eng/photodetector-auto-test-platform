"""Named fault profiles exposed by the simulator."""
PROFILES = ("normal", "high_dark_current", "low_responsivity", "noisy", "nonlinear", "open_circuit", "short_circuit", "communication_error", "unstable", "spectral_mismatch")
PROFILE_DESCRIPTIONS = {
    "normal": "参数位于正常离散范围",
    "high_dark_current": "反向暗电流超过规格",
    "low_responsivity": "光电响应度低于规格",
    "noisy": "电磁干扰或接触不稳导致噪声和重复性变差",
    "nonlinear": "高光功率下响应开始饱和",
    "open_circuit": "开路导致电学和光学响应接近零",
    "short_circuit": "短路电流触发仪器保护限值",
    "communication_error": "虚拟仪器发生连接超时",
    "unstable": "光响应在稳定性测试中持续漂移",
    "spectral_mismatch": "光谱峰值偏离目标波长",
}
