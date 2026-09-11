"""Dependency-free HTML report generator."""
from __future__ import annotations
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from src.domain import DutResult
from src.analysis.metric_catalog import FAILURE_EXPLANATIONS, PROFILE_NAMES, STATUS_NAMES, display_metric_name, metric_guide_rows

def generate_html_report(path: str | Path, run_id: str, results: list[DutResult], summary: dict, plan: dict) -> Path:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        m = r.metrics
        anomaly = "是" if m.get("batch_anomaly") else "否"
        rows.append(
            f"<tr><td>{escape(r.dut_id)}</td><td>{escape(PROFILE_NAMES.get(r.profile, r.profile))}</td>"
            f"<td class='{r.status.lower()}'>{escape(STATUS_NAMES.get(r.status, r.status))}</td><td>{anomaly}</td>"
            f"<td>{_fmt(m.get('dark_current_a'))}</td><td>{_fmt(m.get('responsivity_a_per_w'))}</td>"
            f"<td>{_fmt(m.get('noise_rms_a'))}</td><td>{_fmt(m.get('nep_w_per_sqrt_hz'))}</td>"
            f"<td>{_fmt(m.get('detectivity_jones'))}</td><td>{_fmt(m.get('linearity_r_squared'))}</td>"
            f"<td>{_pct(m.get('repeatability_cv'))}</td><td>{_pct(m.get('stability_drift_fraction'))}</td>"
            f"<td>{_fmt(m.get('spectral_peak_wavelength_nm'))}</td><td>{escape('; '.join(r.reasons) or '-')}</td></tr>"
        )
    reasons = "".join(f"<li>{escape(k)}: {v}</li>" for k, v in summary["failure_reasons"].items()) or "<li>None</li>"
    reason_help = "".join(f"<li><b>{escape(reason)}</b>：{escape(FAILURE_EXPLANATIONS.get(reason, '请结合原始数据和日志复核。'))}</li>" for reason in summary["failure_reasons"])
    anomalies = "".join(
        f"<tr><td>{escape(item['dut_id'])}</td><td>{escape(STATUS_NAMES.get(item['status'], item['status']))}</td><td>{item['score']:.2f}</td><td>{escape('、'.join(display_metric_name(key) for key in item['metrics']))}</td></tr>"
        for item in summary.get("anomaly_duts", [])
    ) or "<tr><td colspan='4'>未发现批次异常器件</td></tr>"
    guide_rows = "".join(f"<tr><td>{escape(row['指标'])}</td><td>{escape(row['单位'])}</td><td>{escape(row['通俗解释'])}</td><td>{escape(row['失败后优先检查'])}</td></tr>" for row in metric_guide_rows())
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Photodetector Test Report</title><style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;max-width:1150px;margin:32px auto;color:#172033}} h1{{margin-bottom:4px}} .notice{{background:#fff3cd;padding:12px;border-left:5px solid #e0a800}} .cards{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}} .card{{padding:14px 20px;background:#f3f6fb;border-radius:8px;min-width:120px}} table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border:1px solid #dfe4ea;padding:8px;text-align:left}} th{{background:#edf2f7}} .pass{{color:#087f5b;font-weight:bold}} .fail{{color:#c92a2a;font-weight:bold}} .error{{color:#9c36b5;font-weight:bold}} footer{{margin-top:24px;color:#667085;font-size:12px}}</style></head><body>
<h1>光电探测器自动化测试与批次质量报告</h1><div>运行编号：{escape(run_id)}　|　追溯种子：{plan.get('random_seed')}　|　模式：{'现实波动' if plan.get('simulation_run_mode') == 'realistic_variation' else '教学复现'}</div><p class='notice'><b>真实性声明：</b>本报告采用参考真实量级的教学仿真模型，仅用于验证自动测试流程，不代表某个具体型号或真实器件测量结果。</p>
<div class='cards'><div class='card'>总数<br><b>{summary['total']}</b></div><div class='card'>PASS<br><b>{summary['pass']}</b></div><div class='card'>FAIL<br><b>{summary['fail']}</b></div><div class='card'>ERROR<br><b>{summary['error']}</b></div><div class='card'>有效测试良率<br><b>{summary['yield_excluding_errors']:.1%}</b></div><div class='card'>批次异常<br><b>{summary.get('anomaly_count', 0)}</b></div></div>
<h2>质量结论</h2><p>系统已完成数据清洗、参数计算、规格判定、失败归因和批次异常筛查。FAIL 表示测量有效但至少一个指标越限；ERROR 表示测试系统未形成有效器件结论；批次异常表示相对同批器件存在统计离群，需要复核。</p>
<h2>DUT 综合结果</h2><div style='overflow-x:auto'><table><thead><tr><th>DUT</th><th>故障配置</th><th>状态</th><th>异常</th><th>暗电流/A</th><th>响应度/A·W⁻¹</th><th>噪声RMS/A</th><th>NEP/W·Hz⁻½</th><th>D*/Jones</th><th>线性R²</th><th>重复性CV</th><th>稳定性漂移</th><th>光谱峰值/nm</th><th>失败原因</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>批次异常器件</h2><table><thead><tr><th>DUT</th><th>状态</th><th>异常分数</th><th>贡献指标</th></tr></thead><tbody>{anomalies}</tbody></table>
<h2>失败原因 Pareto</h2><ul>{reasons}</ul><h3>失败代表什么</h3><ul>{reason_help}</ul>
<h2>指标口径</h2><ul><li>NEP = 输入等效噪声电流密度 / 响应度。</li><li>D* = √有效面积 / NEP，单位 Jones。</li><li>线性度由多光功率点线性拟合的 R² 和满量程最大偏差评价。</li><li>稳定性为模拟时间序列首尾漂移及极差；光谱响应由多波长扫描提取峰值。</li></ul>
<h2>指标学习说明</h2><table><thead><tr><th>指标</th><th>单位</th><th>通俗解释</th><th>不合格后优先检查</th></tr></thead><tbody>{guide_rows}</tbody></table>
<h2>测试配置摘要</h2><p>参考模型：{escape(str(plan.get('detector', {}).get('reference_family', '-')))}</p><pre>{escape(str(plan))}</pre>
<footer>生成时间 {datetime.now(timezone.utc).isoformat()} · 软件版本 0.3.0-sim</footer></body></html>"""
    target.write_text(html, encoding="utf-8")
    return target

def _fmt(value) -> str:
    return "-" if value is None else f"{float(value):.4e}"

def _pct(value) -> str:
    return "-" if value is None else f"{float(value):.2%}"
