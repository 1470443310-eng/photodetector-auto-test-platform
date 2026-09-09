"""Dependency-free HTML report generator."""
from __future__ import annotations
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from src.domain import DutResult

def generate_html_report(path: str | Path, run_id: str, results: list[DutResult], summary: dict, plan: dict) -> Path:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        m = r.metrics
        rows.append(f"<tr><td>{escape(r.dut_id)}</td><td>{escape(r.profile)}</td><td class='{r.status.lower()}'>{r.status}</td><td>{_fmt(m.get('dark_current_a'))}</td><td>{_fmt(m.get('responsivity_a_per_w'))}</td><td>{_fmt(m.get('repeatability_cv'))}</td><td>{escape('; '.join(r.reasons) or '-')}</td></tr>")
    reasons = "".join(f"<li>{escape(k)}: {v}</li>" for k, v in summary["failure_reasons"].items()) or "<li>None</li>"
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Photodetector Test Report</title><style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;max-width:1150px;margin:32px auto;color:#172033}} h1{{margin-bottom:4px}} .notice{{background:#fff3cd;padding:12px;border-left:5px solid #e0a800}} .cards{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}} .card{{padding:14px 20px;background:#f3f6fb;border-radius:8px;min-width:120px}} table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border:1px solid #dfe4ea;padding:8px;text-align:left}} th{{background:#edf2f7}} .pass{{color:#087f5b;font-weight:bold}} .fail{{color:#c92a2a;font-weight:bold}} .error{{color:#9c36b5;font-weight:bold}} footer{{margin-top:24px;color:#667085;font-size:12px}}</style></head><body>
<h1>光电探测器自动化测试报告</h1><div>Run ID: {escape(run_id)}</div><p class='notice'><b>真实性声明：</b>本报告全部数据由简化物理模型生成，仅用于验证自动测试软件，不代表真实器件测量结果。</p>
<div class='cards'><div class='card'>总数<br><b>{summary['total']}</b></div><div class='card'>PASS<br><b>{summary['pass']}</b></div><div class='card'>FAIL<br><b>{summary['fail']}</b></div><div class='card'>ERROR<br><b>{summary['error']}</b></div><div class='card'>有效测试良率<br><b>{summary['yield_excluding_errors']:.1%}</b></div></div>
<h2>DUT结果</h2><table><thead><tr><th>DUT</th><th>故障配置</th><th>状态</th><th>暗电流/A</th><th>响应度/A·W⁻¹</th><th>重复性CV</th><th>原因</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>失败原因统计</h2><ul>{reasons}</ul><h2>测试配置摘要</h2><pre>{escape(str(plan))}</pre>
<footer>Generated {datetime.now(timezone.utc).isoformat()} · Software version 0.1.0</footer></body></html>"""
    target.write_text(html, encoding="utf-8")
    return target

def _fmt(value) -> str:
    return "-" if value is None else f"{float(value):.4e}"
