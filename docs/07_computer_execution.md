# 电脑端落实清单

1. 安装 Python 3.10–3.12 与 Git，克隆或解压项目。
2. 创建 `.venv`，先安装 `requirements-core.txt`。
3. 执行 `python -m pytest`，保存终端输出。
4. 执行 `python scripts/run_demo.py`，打开生成的 HTML 报告。
5. 安装 `requirements.txt`，执行 `streamlit run app.py`。
6. 新建本人 Git 分支；修改一个规格，预测结果后再运行。
7. 选择一个故障，记录“现象—假设—定位—修复—回归”。
8. 确定真实器件型号，依据 datasheet 修改阈值并记录来源。
9. 确定 SMU/光源型号，安装 `requirements-instruments.txt`，按编程手册实现命令。
10. 真机首次运行使用低电压和小 Compliance，先空载/标准件验证，再接 DUT。
