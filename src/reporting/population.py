"""Auditable population statistics and portable SVG figures, without extra dependencies."""
from html import escape
import math
import statistics
import base64
import re


def browser_report(html):
    """Streamlit's HTML-only sanitizer strips inline SVG; image sources preserve it."""
    def image(match):
        svg = match.group(0).replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        label = re.search(r"aria-label='([^']*)'", svg)
        alt = label.group(1) if label else '批次统计图'
        data = base64.b64encode(svg.encode('utf-8')).decode('ascii')
        return f'<img alt="{escape(alt, quote=True)}" src="data:image/svg+xml;base64,{data}" style="width:100%;max-width:700px" />'
    return re.sub(r'<svg\b.*?</svg>', image, html, flags=re.DOTALL)


METRICS = [
    ("dark_current_a", "暗电流", "nA", 1e9, None, "dark_current_max_a", True),
    ("responsivity_a_per_w", "响应度", "A/W", 1, "responsivity_min_a_per_w", "responsivity_max_a_per_w", False),
    ("noise_rms_a", "暗噪声 RMS", "pA", 1e12, None, "noise_rms_max_a", True),
    ("nep_w_per_sqrt_hz", "NEP", "W/√Hz", 1, None, "nep_max_w_per_sqrt_hz", True),
    ("detectivity_jones", "比探测率 D*", "Jones", 1, "detectivity_min_jones", None, True),
    ("repeatability_cv", "重复性 CV", "%", 100, None, "repeatability_cv_max", False),
    ("linearity_r_squared", "线性 R²", "", 1, "linearity_r_squared_min", None, False),
    ("stability_drift_fraction", "稳定性漂移", "%", 100, None, "stability_drift_max_fraction", False),
]
COLORS = {"PASS": "#087f5b", "FAIL": "#d94841", "ERROR": "#805ad5"}


def metric_population(results, key):
    """Exclude ERROR and non-finite/missing values; never replace them with zero."""
    points = []
    for result in results:
        value = result.metrics.get(key)
        if result.status not in ("PASS", "FAIL") or not isinstance(value, (int, float)):
            continue
        if math.isfinite(value):
            points.append((result.dut_id, result.status, float(value)))
    values = [p[2] for p in points]
    return {"points": points, "n": len(values), "excluded": len(results) - len(values),
            "mean": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "stdev": statistics.stdev(values) if len(values) > 1 else None}


def histogram(values, bins=8):
    if not values:
        return [], []
    low, high = min(values), max(values)
    if low == high:
        margin = max(abs(low) * .05, .5)
        low, high = low - margin, high + margin
    edges = [low + (high - low) * i / bins for i in range(bins + 1)]
    counts = [0] * bins
    for value in values:
        counts[min(bins - 1, max(0, int((value - low) / (high - low) * bins)))] += 1
    return edges, counts


def provenance_html(plan, run_id, results):
    mode = "按配置概率抽样器件类型" if plan.get("simulation_run_mode") == "realistic_variation" else "固定教学器件序列"
    measurement, light = plan["measurement"], plan["illumination"]
    return f"""<section><h2>数据集来源与复现</h2>
<p><b>数据类型：程序生成的教学仿真数据，未采集真实器件，也未下载公开测量数据集。</b>
通用硅 PIN 模型以二极管电流、并联漏电、光生电流和噪声生成测量点；再经虚拟 SMU、清洗和参数提取得到每颗器件的指标。</p>
<p>批次 {escape(str(run_id))}；样本数 {len(results)} 颗；种子 {escape(str(plan.get('random_seed')))}；{mode}。
两种模式都包含由种子控制的制造离散、温度及仪器误差。故障比例为教学配置，不是工厂缺陷率。</p>
<p>参考偏压 {measurement['reference_bias_v']} V；波长 {light['wavelength_nm']} nm；光功率 {float(light['optical_power_w']) * 1e6:g} μW；
标称温度 {plan['environment']['nominal_temperature_c']} °C；带宽 {plan['noise']['bandwidth_hz']} Hz；面积 {plan['detector']['active_area_cm2']} cm²。</p>
<p>量级参考：<a href='https://www.vishay.com/docs/81521/bpw34.pdf'>Vishay BPW34 数据手册</a>；
<a href='https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/si_pd_kspd9001e.pdf'>Hamamatsu 硅光电二极管技术说明</a>。
这些资料是背景参考，不是本批数据来源；本模型和质量阈值是教学假设，不是对上述器件规格的逐项复刻。</p>
<p>源码追溯：src/dut/photodiode_model.py → src/sequences/test_sequence.py → src/analysis/parameter_extraction.py。
复现需保存同版本代码、完整生效配置（含模式和种子），用 run_batch(plan) 重算。</p></section>"""


def population_html(results, plan, run_id):
    parts = [provenance_html(plan, run_id, results), "<h2>整体样本与良率分布</h2>"]
    counts = {status: sum(r.status == status for r in results) for status in COLORS}
    total = len(results)
    valid = counts['PASS'] + counts['FAIL']
    pct = lambda num, den: f"{num / den:.1%}" if den else "无有效分母"
    parts.append(f"<p>首测良率 = PASS / 总数 = {counts['PASS']}/{total}（{pct(counts['PASS'], total)}）；"
                 f"有效良率 = PASS / (PASS + FAIL) = {counts['PASS']}/{valid}（{pct(counts['PASS'], valid)}）。"
                 "ERROR 单列为测试异常，不解释为器件不合格。当前仅展示本批统计，不是多批次良率概率分布。</p>")
    parts.append("<svg viewBox='0 0 640 150' role='img' aria-label='PASS FAIL ERROR 数量分布' style='width:100%;max-width:700px'>")
    for i, (status, count) in enumerate(counts.items()):
        y = 8 + i * 46
        parts.append(f"<text x='0' y='{y+23}'>{status}</text><rect x='75' y='{y}' width='{440*count/max(total,1)}' height='30' fill='{COLORS[status]}'/>"
                     f"<text x='{85+440*count/max(total,1)}' y='{y+23}'>{count} 颗 ({pct(count,total)})</text>")
    parts.append("</svg><h2>全样本指标分布与规格对照</h2><p>每颗器件贡献一个指标值；包含 PASS 和 FAIL，排除 ERROR 及缺失/非有限值。"
                 "柱形图显示频数；下方逐颗散点保留异常样本。绿色为整颗 PASS，红色为整颗 FAIL，颜色不代表该单项一定越限。"
                 "虚线为本次配置规格。跨度较大的正值使用 log10 坐标，刻度仍显示原单位；非正值存在时保留全部数据并使用线性坐标。"
                 "分布图用于检查覆盖范围与判定一致性，不能单独证明算法准确性或真实制造良率。</p>")
    parts.append("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,440px),1fr));gap:18px'>")
    for key, label, unit, scale, lower, upper, prefer_log in METRICS:
        pop = metric_population(results, key)
        points = pop['points']
        parts.append(f"<section style='border:1px solid #dfe4ea;border-radius:10px;padding:12px;min-width:0'><h3>{label} ({unit})</h3>"
                     f"<p>有效 n={pop['n']}；排除 {pop['excluded']} 颗</p>")
        if not points:
            parts.append("<p>无有效测量数据</p></section>")
            continue
        values = [p[2] * scale for p in points]
        limits = [(name, float(plan['limits'][bound]) * scale) for name, bound in [('下限', lower), ('上限', upper)] if bound and bound in plan['limits']]
        log = prefer_log and all(v > 0 for v in values + [v for _, v in limits])
        transform = math.log10 if log else lambda v: v
        transformed = [transform(v) for v in values]
        edges, bins = histogram(transformed)
        lo = min([edges[0]] + [transform(v) for _, v in limits])
        hi = max([edges[-1]] + [transform(v) for _, v in limits])
        pad = (hi-lo) * .07
        lo, hi = lo-pad, hi+pad
        x = lambda v: 48 + 430 * (v-lo)/(hi-lo)
        parts.append(f"<svg viewBox='0 0 530 275' role='img' aria-label='{label}全样本频数和逐颗散点' style='width:100%'>"
                     "<text x='4' y='18' font-size='12'>颗数</text>")
        peak = max(bins)
        for i, count in enumerate(bins):
            left, right = x(edges[i]), x(edges[i+1])
            height = 108*count/peak
            parts.append(f"<rect x='{left:.2f}' y='{140-height:.2f}' width='{max(right-left-1, .1):.2f}' height='{height:.2f}' fill='#3278b7'/>"
                         f"<text x='{(left+right)/2:.2f}' y='{134-height:.2f}' text-anchor='middle' font-size='11'>{count}</text>")
        for name, value in limits:
            xpos = x(transform(value))
            parts.append(f"<line x1='{xpos}' x2='{xpos}' y1='30' y2='222' stroke='#c05621' stroke-dasharray='5 4'/>"
                         f"<title>{name}: {value:g} {unit}</title>")
        for i, (dut, status, value) in enumerate(points):
            parts.append(f"<circle cx='{x(transform(value*scale))}' cy='{180+(i%4)*11}' r='4' fill='{COLORS[status]}'>"
                         f"<title>{escape(dut)} {status}: {value*scale:.5g} {unit}</title></circle>")
        parts.append("<line x1='48' x2='478' y1='225' y2='225' stroke='#667085'/>")
        for i in range(5):
            tick = lo+(hi-lo)*i/4
            actual = 10**tick if log else tick
            parts.append(f"<text x='{x(tick)}' y='243' text-anchor='middle' font-size='11'>{actual:.2g}</text>")
        parts.append(f"<text x='265' y='267' text-anchor='middle' font-size='12'>{unit} · {'log10 坐标' if log else '线性坐标'}</text></svg>")
        sd = f"{pop['stdev']*scale:.4g}" if pop['stdev'] is not None else '不可估计（n&lt;2）'
        parts.append(f"<p>均值 {pop['mean']*scale:.4g}；中位数 {pop['median']*scale:.4g}；样本标准差 {sd}。<br>"
                     + '；'.join(f"{name} {v:g} {unit}" for name, v in limits) + "</p></section>")
    parts.append("</div>")
    return ''.join(parts)
