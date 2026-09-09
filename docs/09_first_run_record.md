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
