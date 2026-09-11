# Codex 项目交接说明

## 项目目标

本项目是面向光电信息科学与工程本科生、半导体测试开发岗位的作品 Demo：基于虚拟仪器完成光电二极管 I-V、响应度、噪声、NEP、探测率、线性度、重复性、稳定性、光谱响应、三态判定、批量异常检测和自动报告，并逐步迁移到真实 VISA/SCPI 仪器。

## 当前基线

- 版本：v0.3.0 现实量级教学仿真版
- Python 基线：3.12.14
- 自动化测试：19 passed
- 样例批次：20 DUT；PASS 13、FAIL 6、ERROR 1
- 样例产物：`sample_data/`
- 项目状态：`PROJECT_STATUS.md`
- 正式立项书：`docs/00_project_charter.md`

所有当前测量结果均为简化模型仿真数据，不得写成真实器件实验结果。`VisaSMU` 仅为通用适配骨架，未经过硬件验证。

## 首次进入项目

先阅读：

1. `README.md`
2. `PROJECT_STATUS.md`
3. `docs/00_project_charter.md`
4. `docs/06_test_theory.md`
5. `docs/07_computer_execution.md`

Windows PowerShell 建议命令：

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-core.txt
python -m pytest
python scripts/run_demo.py
```

## 后续开发优先级

1. 已在用户电脑复现 19 项测试、20 DUT 基线、现实波动/教学复现双模式、主页面中文报告、右上角说明、匿名反馈和临时公网访问。
2. 让用户本人修改一项阈值，预测、运行并解释结果。
3. 让用户主动制造一个故障，完成定位、修复和回归记录。
4. 选择真实光电二极管、SMU 与光源型号后，依据 datasheet 和编程手册修改参数及 SCPI 命令。
5. 整理 Git 提交记录、演示视频和博士审阅包。

## 工程约束

- 保持 PASS、FAIL、ERROR 含义分离。
- 新功能必须补测试，不以界面代替核心测试逻辑。
- 使用固定随机种子保证仿真可复现。
- 不覆盖用户填写的 `docs/04_personal_contribution.md`。
- 未有真实硬件证据前，不得宣称完成真实仪器测试。
- 修改模型或阈值后，更新测试、样例数据和运行记录。
