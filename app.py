"""Streamlit quality dashboard. Run with: streamlit run app.py"""
from pathlib import Path
import hmac
import os
import uuid
import streamlit as st
from src.pipeline import execute
from src.analysis.metric_catalog import (
    FAILURE_EXPLANATIONS, METRIC_CATALOG, PROFILE_NAMES, STATUS_NAMES,
    display_metric_name, metric_assessment, metric_guide_rows,
)
from src.storage.feedback import feedback_summary, save_feedback

st.set_page_config(page_title="Photodetector Quality Platform", layout="wide")

GUIDE_DOC = Path("docs/10_realistic_simulation_and_student_guide.md")


def cloud_setting(name: str, default: str = "") -> str:
    """Read local environment variables or Streamlit Community Cloud secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, KeyError):
        return default


FEEDBACK_DB = cloud_setting("DATABASE_URL") or Path("artifacts/test_results.sqlite3")

header_main, header_guide = st.columns([5, 1], vertical_alignment="top")
with header_main:
    st.title("光电探测器自动化测试与质量分析平台")
with header_guide:
    with st.popover("📘 查看说明", use_container_width=True):
        st.markdown(GUIDE_DOC.read_text(encoding="utf-8"))
st.warning("当前为简化物理模型仿真，数据只用于验证测试流程，不代表真实器件测量。")
st.caption("完整链路：DUT → 虚拟仪器 → 自动采集 → 数据清洗 → 参数计算 → 性能判定 → Batch分析 → 异常检测 → Quality Report")

page = st.sidebar.radio("功能导航", ["自动测试平台", "用户试用反馈", "管理员反馈汇总"])

if page == "用户试用反馈":
    st.header("匿名试用反馈")
    st.info("我们不要求姓名、手机号、学校或其他身份信息。反馈仅用于改进这个测试 Demo。请勿在意见中填写个人敏感信息。")
    if "anonymous_feedback_session" not in st.session_state:
        st.session_state["anonymous_feedback_session"] = uuid.uuid4().hex[:12]
    with st.form("feedback_form", clear_on_submit=True):
        rating = st.slider("整体使用体验评分", 1, 5, 4)
        st.write("请勾选你实际完成的任务：")
        completed_run = st.checkbox("成功运行了20个DUT测试")
        found_fail_reason = st.checkbox("找到了某颗探测器 FAIL 的原因")
        understood_report = st.checkbox("理解了 Quality Report 的主要结论")
        found_anomaly = st.checkbox("找到了 Batch 中的异常器件")
        difficult_metric = st.selectbox("最难理解的指标", ["", "暗电流", "响应度", "噪声", "NEP", "探测率D*", "线性度", "重复性", "稳定性", "光谱响应", "Batch异常分数"])
        comments = st.text_area("遇到的问题或改进建议（最多2000字）", max_chars=2000)
        submitted = st.form_submit_button("匿名提交反馈", type="primary")
    if submitted:
        feedback_id = save_feedback(
            FEEDBACK_DB, st.session_state["anonymous_feedback_session"], rating,
            {"completed_run": completed_run, "found_fail_reason": found_fail_reason,
             "understood_report": understood_report, "found_anomaly": found_anomaly},
            difficult_metric, comments,
        )
        st.success(f"感谢反馈，已匿名保存。反馈编号：{feedback_id[:8]}")
    st.stop()

if page == "管理员反馈汇总":
    st.header("管理员反馈汇总")
    configured_password = cloud_setting("PHOTO_TEST_ADMIN_PASSWORD")
    if not configured_password:
        st.error("管理员密码尚未配置。请设置环境变量 PHOTO_TEST_ADMIN_PASSWORD 后重启服务。")
        st.stop()
    supplied_password = st.text_input("管理员密码", type="password")
    if not supplied_password or not hmac.compare_digest(supplied_password, configured_password):
        st.info("输入管理员密码后查看匿名汇总。")
        st.stop()
    summary_feedback = feedback_summary(FEEDBACK_DB)
    admin_cols = st.columns(2)
    admin_cols[0].metric("反馈数量", summary_feedback["total"])
    admin_cols[1].metric("平均评分", f"{summary_feedback['average_rating']:.2f} / 5")
    st.subheader("任务完成率")
    task_labels = {"completed_run": "运行测试", "found_fail_reason": "找到FAIL原因", "understood_report": "理解报告", "found_anomaly": "找到异常器件"}
    task_rows = [{"任务": task_labels[key], "完成率": value} for key, value in summary_feedback["task_completion_rates"].items()]
    st.dataframe(task_rows, use_container_width=True, hide_index=True)
    st.subheader("评分分布")
    rating_rows = [{"评分": str(key), "人数": value} for key, value in summary_feedback["rating_distribution"].items()]
    st.bar_chart(rating_rows, x="评分", y="人数")
    st.subheader("最难理解的指标")
    difficult_rows = [{"指标": key, "人数": value} for key, value in summary_feedback["difficult_metrics"].items()]
    st.dataframe(difficult_rows, use_container_width=True, hide_index=True)
    st.subheader("匿名反馈明细")
    display_rows = [{"时间": row["created_at"], "评分": row["overall_rating"], "最难指标": row["difficult_metric"], "意见": row["comments"], "版本": row["app_version"]} for row in summary_feedback["rows"]]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    st.download_button("下载反馈 JSON", data=__import__("json").dumps(summary_feedback["rows"], ensure_ascii=False, indent=2), file_name="anonymous_feedback.json", mime="application/json")
    st.stop()

config = st.sidebar.text_input("测试方案", "configs/default_test_plan.yaml")
data_mode = st.sidebar.radio(
    "仿真数据模式",
    ["现实波动模式（每次不同）", "教学复现模式（每次相同）"],
    help="现实波动模式会为每个批次生成新种子并模拟制造离散、温度及仪器误差；教学复现模式使用固定种子，便于调试和复核。",
)
run_requested = st.sidebar.button("运行完整20 DUT测试", type="primary")

if run_requested:
    with st.spinner("执行 I–V、噪声、线性度、重复性、稳定性和光谱响应测试…"):
        previous_outcome = st.session_state.get("outcome")
        new_outcome = execute(config, randomize_seed=data_mode.startswith("现实波动"))
        new_outcome["previous_effective_seed"] = (
            previous_outcome.get("effective_seed") if previous_outcome else None
        )
        new_outcome["browser_run_count"] = (
            previous_outcome.get("browser_run_count", 0) + 1 if previous_outcome else 1
        )
        st.session_state["outcome"] = new_outcome

outcome = st.session_state.get("outcome")
if not outcome:
    st.info("点击左侧按钮启动完整测试链路。命令行入口为 scripts/run_demo.py。")
    st.stop()

summary = outcome["summary"]
is_realistic = outcome["simulation_run_mode"] == "realistic_variation"
previous_seed = outcome.get("previous_effective_seed")
seed_check = (
    "首次运行" if previous_seed is None
    else "已变化" if previous_seed != outcome["effective_seed"]
    else "保持相同（教学复现）"
)
st.caption(
    f"本批运行模式：{'现实波动' if is_realistic else '教学复现'}　｜　"
    f"页面内第 {outcome.get('browser_run_count', 1)} 次运行　｜　"
    f"本次种子：{outcome['effective_seed']}　｜　上次种子：{previous_seed or '无'}　｜　{seed_check}　｜　"
    f"参考模型：{outcome['plan']['detector']['reference_family']}"
)
if is_realistic:
    st.info("现实波动模式每次点击都会重新生成器件制造离散、温度和仪器误差；可用上方种子确认本次数据是否已经更新。")
cols = st.columns(6)
values = [summary["total"], summary["pass"], summary["fail"], summary["error"], f"{summary['yield_excluding_errors']:.1%}", summary["anomaly_count"]]
for col, label, value in zip(cols, ["总数", "PASS", "FAIL", "ERROR", "有效良率", "批次异常"], values):
    col.metric(label, value)

st.header("本次中文质量报告")
if summary["error"]:
    report_level = st.warning
elif summary["fail"]:
    report_level = st.info
else:
    report_level = st.success
report_level(
    f"本批共测试 {summary['total']} 颗：通过 {summary['pass']} 颗、不合格 {summary['fail']} 颗、"
    f"测试异常 {summary['error']} 颗；有效良率 {summary['yield_excluding_errors']:.1%}，"
    f"识别出 {summary['anomaly_count']} 颗批次异常器件。"
)
st.caption("报告已在测试结束后自动生成并直接显示在主页面；下方仍可继续查看单颗曲线、失败原因和批次统计。")
report_html = Path(outcome["report"]).read_text(encoding="utf-8")
st.download_button(
    "下载本次中文质量报告",
    data=report_html,
    file_name=Path(outcome["report"]).name,
    mime="text/html",
)
st.html(report_html)

overview_tab, curves_tab, batch_tab, guide_tab = st.tabs(["探测器综合判定", "单颗曲线与指标", "批次质量分析", "指标学习说明"])

with overview_tab:
    rows = []
    for result in outcome["results"]:
        m = result.metrics
        rows.append({
            "探测器编号": result.dut_id, "模拟状态": PROFILE_NAMES.get(result.profile, result.profile), "判定": STATUS_NAMES.get(result.status, result.status),
            "批次异常": "是" if m.get("batch_anomaly") else "否", "暗电流(A)": m.get("dark_current_a"),
            "响应度(A/W)": m.get("responsivity_a_per_w"), "噪声RMS(A)": m.get("noise_rms_a"),
            "NEP(W/√Hz)": m.get("nep_w_per_sqrt_hz"), "D*(Jones)": m.get("detectivity_jones"),
            "线性R²": m.get("linearity_r_squared"), "线性最大误差": m.get("linearity_max_error_fraction"),
            "重复性CV": m.get("repeatability_cv"), "稳定性漂移": m.get("stability_drift_fraction"),
            "光谱峰值(nm)": m.get("spectral_peak_wavelength_nm"), "失败原因": "; ".join(result.reasons),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.info("通过（PASS）= 测试有效且所有指标在规格内；不合格（FAIL）= 测试有效但至少一项越限；测试异常（ERROR）= 仪器或流程异常，不能据此判定器件好坏。")
    with st.expander("为什么每次现实波动模式的数据不同？"):
        st.write("真实器件之间存在制造离散，实验室温度、仪器零点和增益也会变化。本模式每批生成一个新种子，在受控范围内模拟这些变化；报告会保存种子，因此结果仍可追溯。")

with curves_tab:
    selected_id = st.selectbox("选择一颗探测器", [result.dut_id for result in outcome["results"]])
    selected = next(result for result in outcome["results"] if result.dut_id == selected_id)
    st.write(f"**判定：{STATUS_NAMES.get(selected.status, selected.status)}**　模拟状态：{PROFILE_NAMES.get(selected.profile, selected.profile)}　失败原因：{'; '.join(selected.reasons) or '无'}")
    if selected.reasons:
        for reason in selected.reasons:
            st.warning(f"{reason}：{FAILURE_EXPLANATIONS.get(reason, '请结合原始数据和测试日志复核。')}")
    limits = outcome["plan"]["limits"]
    metric_rows = []
    for key, (label, unit, meaning, action) in METRIC_CATALOG.items():
        if key not in selected.metrics:
            continue
        value = float(selected.metrics[key])
        verdict, specification = metric_assessment(key, value, limits)
        metric_rows.append({"指标": label, "数值": value, "单位": unit, "参考规格": specification, "结果": verdict, "代表什么": meaning, "不合格后检查": action})
    st.dataframe(metric_rows, use_container_width=True, hide_index=True)
    if selected.measurements:
        iv = [{"电压(V)": p.voltage_v, "暗态电流(A)": p.current_a if p.mode == "dark_iv" else None, "光照电流(A)": p.current_a if p.mode == "light_iv" else None} for p in selected.measurements if p.mode in ("dark_iv", "light_iv")]
        linearity = [{"入射光功率(W)": p.optical_power_w, "电流绝对值(A)": abs(p.current_a)} for p in selected.measurements if p.mode == "linearity"]
        spectral = [{"波长(nm)": p.wavelength_nm, "电流绝对值(A)": abs(p.current_a)} for p in selected.measurements if p.mode == "spectral_response"]
        stability = [{"经过时间(s)": p.elapsed_s, "电流绝对值(A)": abs(p.current_a)} for p in selected.measurements if p.mode == "stability"]
        st.subheader("暗态/光照 I–V")
        st.line_chart(iv, x="电压(V)")
        chart_cols = st.columns(3)
        with chart_cols[0]: st.subheader("线性度"); st.line_chart(linearity, x="入射光功率(W)")
        with chart_cols[1]: st.subheader("光谱响应"); st.line_chart(spectral, x="波长(nm)")
        with chart_cols[2]: st.subheader("稳定性"); st.line_chart(stability, x="经过时间(s)")

with batch_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("失败原因 Pareto")
        reason_rows = [{"原因": key, "数量": value} for key, value in summary["failure_reasons"].items()]
        st.dataframe(reason_rows, use_container_width=True, hide_index=True)
        if reason_rows: st.bar_chart(reason_rows, x="原因", y="数量")
    with right:
        st.subheader("异常器件清单")
        anomaly_rows = [{"探测器编号": item["dut_id"], "判定": STATUS_NAMES.get(item["status"], item["status"]), "异常分数": item["score"], "贡献指标": "、".join(display_metric_name(key) for key in item["metrics"])} for item in summary["anomaly_duts"]]
        st.dataframe(anomaly_rows, use_container_width=True, hide_index=True)
    st.subheader("数据质量")
    quality_rows = [{"DUT": r.dut_id, "原始点": r.metrics.get("raw_point_count"), "清洗后": r.metrics.get("clean_point_count"), "无效点": r.metrics.get("invalid_point_count"), "重复点": r.metrics.get("duplicate_point_count")} for r in outcome["results"]]
    st.dataframe(quality_rows, use_container_width=True, hide_index=True)

with guide_tab:
    st.header("普通光电学生也能读懂的指标说明")
    st.dataframe(metric_guide_rows(), use_container_width=True, hide_index=True)
    st.subheader("判定逻辑")
    st.markdown("- **通过（PASS）**：采集完成，而且全部规格满足。\n- **不合格（FAIL）**：数据有效，但器件或测试状态至少一项超规。\n- **测试异常（ERROR）**：通信、安全互锁等问题导致没有形成有效器件结论。\n- **批次异常**：相对同批器件统计离群，需要复测；它不自动替代规格判定。")
    st.subheader("现实依据与边界")
    st.write("当前是通用硅 PIN 光电二极管教学模型，参数量级参考公开厂商资料。真实产品必须换成具体型号的数据手册、真实光源功率、温度、带宽和校准记录后再制定规格。")
    st.markdown("参考：[Vishay BPW34 数据手册](https://www.vishay.com/docs/81521/bpw34.pdf)；[Hamamatsu Si 光电二极管技术说明](https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/si_pd_kspd9001e.pdf)")
