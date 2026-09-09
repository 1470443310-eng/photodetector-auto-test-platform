# 基于虚拟仪器的光电探测器自动化测试与质量分析平台

Automated Photodetector Test and Quality Analysis Platform

面向光电与半导体测试开发岗位的本科生工程 Demo。平台在没有真实硬件时，通过可复现的光电二极管模型和虚拟仪器完成批量暗态 I–V、光照 I–V、响应度、重复性、规格判定、质量统计和报告归档；后续可通过统一接口替换为真实 VISA/SCPI 仪器。

> **真实性声明：** 当前结果全部是仿真数据，用于验证软件架构和测试流程，不能写成真实实验结论。真实仪器适配器尚未完成硬件验证。

## 已实现功能

- YAML 可配置的电压扫描、采样、光功率和质量阈值
- 正常、暗电流偏大、低响应、强噪声、非线性、开路、短路、通信异常模型
- 暗态 I–V、光照 I–V、响应度和重复性自动测试
- 电压安全互锁、电流 Compliance 和通信异常
- PASS、FAIL、ERROR 三态判定
- 20 个 DUT 批量运行与良率、失败原因统计
- CSV、JSON、SQLite、日志和独立 HTML 报告
- 固定随机种子复现结果
- pytest 单元与端到端测试
- Streamlit 演示界面和无界面的命令行入口

## 快速运行

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-core.txt
python scripts/run_demo.py
```

启动界面：

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux 将激活命令替换为 `source .venv/bin/activate`。输出保存在 `artifacts/SIM-时间戳/`，汇总数据库位于 `artifacts/test_results.sqlite3`。

## 自动化验证

```bash
python -m pytest
```

## 目录导航

| 路径 | 内容 |
|---|---|
| `docs/00_project_charter.md` | 正式立项书 |
| `configs/` | 测试方案和仪器配置 |
| `src/dut/` | 器件与故障模型 |
| `src/instruments/` | 虚拟与真实仪器接口 |
| `src/sequences/` | 自动测试序列 |
| `src/analysis/` | 参数提取、判定和批次统计 |
| `src/storage/` | CSV/JSON/SQLite |
| `src/reporting/` | HTML 报告 |
| `tests/` | 自动化测试 |
| `reviewer/` | 博士审阅材料 |
| `prompts/` | 后续环境、构建、排障、审查提示词 |

## 推荐演示顺序

1. 修改 `configs/default_test_plan.yaml` 中一个阈值。
2. 运行 `python scripts/run_demo.py`。
3. 展示 PASS/FAIL/ERROR、HTML 报告、CSV 原始数据和 SQLite 记录。
4. 运行 `python -m pytest` 展示回归验证。
5. 解释 `SimulatedSMU` 与 `VisaSMU` 如何替换。

详细原理、边界、风险和电脑端步骤见 `docs/`。
