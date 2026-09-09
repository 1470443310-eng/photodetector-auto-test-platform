"""Streamlit dashboard. Run with: streamlit run app.py"""
from pathlib import Path
import streamlit as st
from src.pipeline import execute

st.set_page_config(page_title="Photodetector Auto Test", layout="wide")
st.title("光电探测器自动化测试与质量分析平台")
st.warning("当前为物理模型仿真模式，数据不代表真实器件测量。")
config = st.sidebar.text_input("测试方案", "configs/default_test_plan.yaml")
if st.sidebar.button("运行20个DUT", type="primary"):
    with st.spinner("执行暗态、光照与重复性测试…"):
        outcome = execute(config)
    summary = outcome["summary"]
    cols = st.columns(5)
    for col, label, value in zip(cols, ["总数", "PASS", "FAIL", "ERROR", "有效良率"], [summary["total"], summary["pass"], summary["fail"], summary["error"], f"{summary['yield_excluding_errors']:.1%}"]):
        col.metric(label, value)
    rows = []
    for result in outcome["results"]:
        rows.append({"DUT": result.dut_id, "Profile": result.profile, "Status": result.status, "Dark current (A)": result.metrics.get("dark_current_a"), "Responsivity (A/W)": result.metrics.get("responsivity_a_per_w"), "Reasons": "; ".join(result.reasons)})
    st.dataframe(rows, use_container_width=True)
    st.success(f"报告已生成：{outcome['report']}")
    st.html(Path(outcome["report"]).read_text(encoding="utf-8"))
else:
    st.info("在左侧点击“运行20个DUT”开始。命令行版本见 scripts/run_demo.py。")
