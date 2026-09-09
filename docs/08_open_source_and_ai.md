# 开源、AI辅助与个人贡献边界

## 当前直接依赖

- PyYAML：读取测试方案。
- pytest：自动化验证（开发依赖）。
- Streamlit：可选展示界面。
- PyVISA、pyvisa-py、pyvisa-sim：真实/模拟 VISA 通信的可选后续依赖。

版本与许可证应在正式发布前用对应项目官方仓库再次核验，并生成依赖清单。OpenHTF、PyMeasure、Semi-ATE/STDF 当前仅作为架构和进阶方向参考，没有复制其源代码。

## AI辅助声明

初始架构、代码骨架、文档与测试由用户提出目标后在 Codex 辅助下生成。项目不能仅凭这些内容证明用户已独立掌握。用户应亲自完成环境复现、原理核验、参数选择、至少一次功能修改、一次故障定位、Git提交和现场讲解，并在 `04_personal_contribution.md` 留下证据。
