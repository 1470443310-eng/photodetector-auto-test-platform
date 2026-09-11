# 基于虚拟仪器的光电探测器自动化测试与质量分析平台

Automated Photodetector Test and Quality Analysis Platform

面向光电与半导体测试开发岗位的本科生工程 Demo。平台在没有真实硬件时，通过可复现的光电二极管模型和虚拟仪器完成批量暗态 I–V、光照 I–V、响应度、重复性、规格判定、质量统计和报告归档；后续可通过统一接口替换为真实 VISA/SCPI 仪器。

> **真实性声明：** 当前结果全部是仿真数据，用于验证软件架构和测试流程，不能写成真实实验结论。真实仪器适配器尚未完成硬件验证。

## 已实现功能

- YAML 可配置的电压扫描、采样、光功率和质量阈值
- 正常、暗电流偏大、低响应、强噪声、非线性、开路、短路、通信异常模型
- 暗态 I–V、光照 I–V、响应度和重复性自动测试
- 暗噪声、NEP、比探测率 D*、多功率线性度、时间稳定性和光谱响应分析
- 原始数据有效性检查、非有限值剔除、精确重复点去重及清洗审计计数
- 电压安全互锁、电流 Compliance 和通信异常
- PASS、FAIL、ERROR 三态判定
- 20 个 DUT 批量运行、良率、失败原因 Pareto 和稳健统计异常器件识别
- CSV、JSON、SQLite、日志和独立 HTML 报告
- 固定随机种子复现结果
- pytest 单元与端到端测试
- Streamlit 演示界面和无界面的命令行入口
- 测试完成后在主页面直接显示并下载中文质量报告，右上角可随时打开使用说明
- 匿名用户试用反馈、SQLite 保存和密码保护的管理员反馈汇总

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

管理员反馈页需要在启动前设置密码：

```powershell
$env:PHOTO_TEST_ADMIN_PASSWORD = "请替换为强密码"
.venv\Scripts\python.exe -m streamlit run app.py
```

匿名反馈保存在 `artifacts/test_results.sqlite3` 的 `user_feedback` 表中，不主动收集姓名、手机号、学校或 IP。管理员页可查看评分分布、任务完成率、难点指标和文字意见，并下载 JSON。

部署到 Streamlit Community Cloud 时，在应用 Secrets 中设置：

```toml
PHOTO_TEST_ADMIN_PASSWORD = "请替换为强密码"
DATABASE_URL = "postgresql://用户:密码@主机/数据库?sslmode=require"
```

设置 `DATABASE_URL` 后，用户反馈和管理员汇总会自动改用云端 PostgreSQL。Secret 不应写入 GitHub。迁移本机匿名反馈可在本机临时设置同一个 `DATABASE_URL`，再运行 `python scripts/migrate_feedback.py`；脚本按反馈编号去重，可安全重试。

临时公网试用可使用 Cloudflare Quick Tunnel：

```powershell
cloudflared tunnel --url http://127.0.0.1:8501
```

Quick Tunnel 仅用于短期试用，地址随进程结束失效且没有可用性保证；正式部署应使用固定域名、持久数据库、HTTPS、访问控制和备份。

macOS/Linux 将激活命令替换为 `source .venv/bin/activate`。输出保存在 `artifacts/SIM-时间戳/`，汇总数据库位于 `artifacts/test_results.sqlite3`。

## 自动化验证

```bash
python -m pytest
```

当前完整链路为：探测器模型 → 虚拟 SMU/光源 → 自动采集 → 数据清洗 → 参数计算 → 规格判定与失败归因 → Batch 质量统计 → 异常检测 → Quality Report。网页默认使用现实波动模式，每批模拟器件制造离散、温度和仪器误差；教学复现模式继续使用固定种子。默认质量结构保持为 20 DUT、PASS 13、FAIL 6、ERROR 1。

当前自动化回归：19 passed（包含主页面报告、右上角说明入口、连续运行随机种子变化以及反馈迁移幂等性测试）。

## 目录导航

| 路径 | 内容 |
|---|---|
| `docs/00_project_charter.md` | 正式立项书 |
| `docs/10_realistic_simulation_and_student_guide.md` | 现实量级仿真依据、双模式与学生读数指南 |
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
