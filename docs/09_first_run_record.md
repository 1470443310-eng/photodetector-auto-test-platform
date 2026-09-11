# 首次运行与验证记录

- 环境：Linux，Python 3.12.14
- 核心依赖：PyYAML 6.0.2、pytest 8.3.5
- 自动化测试命令：`.venv/bin/python -m pytest`
- 自动化测试结果：`8 passed in 0.07s`
- Demo 命令：`.venv/bin/python scripts/run_demo.py`
- 首次批次规模：20 DUT
- 参数修正后基线结果：PASS 13、FAIL 6、ERROR 1，有效测试良率 68.4%
- 产物：DUT汇总 CSV、原始点 CSV、JSON、SQLite、日志、HTML 报告

说明：第一次试跑发现“非线性”和“噪声”故障强度不足，随后调整模型，使二者分别触发低响应度和重复性失败；回归测试仍为 8 passed。该记录是固定随机种子的仿真证据，不是物理器件实验数据。后续若修改模型或阈值，应重新运行测试并新增记录，不应覆盖成“真实测量”。

## v0.2.0 完整链路复验（2026-09-11）

- 环境：Windows 11，Python 3.12.14，Streamlit 1.43.2。
- 新增：暗噪声、NEP、D*、多功率线性度、时间稳定性、光谱响应、数据清洗审计和批次 MAD 异常检测。
- 自动化测试：`11 passed`。
- Streamlit AppTest：首次加载 0 exception；运行完整 20 DUT 后 0 exception；四个功能页签均生成。
- 20 DUT 基线：PASS 13、FAIL 6、ERROR 1，有效良率 68.4%，批次异常 6。
- 真实性边界：本轮仍为固定种子的简化模型仿真；NEP、D*、带宽、面积、稳定性和光谱数据均非真实硬件测量。

## 匿名反馈与公网试用复验（2026-09-11）

- 新增匿名评分、四项任务完成情况、难点指标和文字意见，保存至 SQLite `user_feedback` 表。
- 新增管理员密码保护、评分分布、任务完成率、难点统计、匿名明细和 JSON 下载。
- 自动化测试：`13 passed`；反馈页和管理员页 Streamlit AppTest 均为 0 exception。
- Cloudflare Quick Tunnel 连通性预检全部 PASS；公网根页面 HTTP 200，`/_stcore/health` 返回 `ok`。
- Quick Tunnel 只作为短期用户试用入口，电脑或隧道关闭后失效，不作为生产部署。

## v0.3.0 现实量级与中文教学版复验（2026-09-11）

- 网页默认现实波动模式：连续两批有效种子分别为 `1361833906` 与 `1230545833`。
- 同一正常器件位置两批响应度约 `0.5395 A/W` 与 `0.5795 A/W`，暗电流约 `2.54 nA` 与 `1.03 nA`，证明批次数据不再固定。
- 正常器件 NEP 约为 `1e-14 W/√Hz` 量级；数量级参考 Vishay BPW34 和 Hamamatsu Si 光电二极管技术资料。
- 教学复现模式种子 `20260909`：PASS 13、FAIL 6、ERROR 1、批次异常 6。
- 自动化测试：`16 passed`，包含“相同种子完全复现”“不同种子产生不同器件参数”“六种教学故障不被正常制造离散掩盖”。
- Streamlit 完整运行：0 exception；五个中文页签均生成。
