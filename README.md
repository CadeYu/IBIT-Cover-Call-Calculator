# HodlYield 🛡️ - Bitcoin Maxi 的备兑策略工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HodlYield** 是一个专为比特币长期持有者 (Bitcoin Maximalists) 设计的辅助工具。它帮助您在持有 IBIT (贝莱德比特币 ETF) 的同时，通过卖出备兑看涨期权 (Covered Call) 安全地赚取额外现金流。

## ✨ 核心理念

1.  **不卖飞 (Hold on for Dear Life)**: 我们的首要目标是保住手中的比特币筹码。
2.  **低风险 (Low Delta)**: 筛选低 Delta (通常 < 0.20) 的期权，极大幅度降低被行权的概率。
3.  **现金流 (Yield)**: 在安全边际内，寻找年化收益率最合理的选项。

## 🚀 功能特点

- **风险可视化**: 通过散点图直观展示 "风险 (Delta)" 与 "回报 (Yield)" 的关系。寻找左上角的 "甜蜜点"。
- **成本保护**: 输入您的持仓成本，系统会自动 **红色高亮** 所有会导致本金亏损的行权价。
- **暗黑模式优化**: 专为夜间交易设计的配色，清晰易读。
- **实时数据**: 基于 Yahoo Finance 的实时美股期权数据。

## 🛠️ 安装与运行

### 前置要求
- Python 3.8 或更高版本

### 步骤

1.  **克隆仓库**
    ```bash
    git clone https://github.com/yourusername/HodlYield.git
    cd HodlYield
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Mac/Linux
    # .venv\Scripts\activate   # Windows
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **运行应用**
    ```bash
    streamlit run app.py
    ```

5.  打开浏览器访问 [http://localhost:8501](http://localhost:8501)

## ☁️ 免费部署 (Deploy)

您可以直接将本项目免费部署到 **Streamlit Community Cloud**，生成一个类似 `https://your-project.streamlit.app` 的网址分享给朋友。

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

### 部署步骤：
1.  **Fork** 本项目到您的 GitHub 账号。
2.  登录 [Streamlit Community Cloud](https://share.streamlit.io/) (使用 GitHub 登录)。
3.  点击 **"New app"**。
4.  选择刚刚 Fork 的仓库 `HodlYield`。
5.  **关键设置**:
    - **Main file path**: 输入 `HodlYield/app.py` (注意：因为代码在子文件夹里)。
6.  点击 **"Deploy!"**。
7.  等待几分钟，您的专属链接就生成了！

## 📊 使用指南

1.  **Ticker**: 默认为 `IBIT`。
2.  **Cost Basis**: **强烈建议** 输入您的平均持仓成本。低于此价格的行权价会被标记为红色，防止亏损卖出。
3.  **Max Delta**: 设置您能承受的最大风险。建议保守型投资者设为 0.15 - 0.20。
4.  **看图表**:
    *   **X轴**: 风险 (Delta)。越左越安全。
    *   **Y轴**: 年化收益率。越上越赚钱。
    *   **策略**: 找左上角的点。

## ⚠️ 免责声明

本工具仅用于数据分析与教育目的，**不构成任何投资建议**。期权交易具有风险，甚至可能导致亏损。请在交易前自行做好研究 (DYOR)。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。欢迎所以比特币信仰者共同改进。
