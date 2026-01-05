# Affiliate Commerce KPI & ROI Tracker 📊


**New York Post Commerce Data Analyst Portfolio Project**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ajaykasu1-pro-ak-pj-srcdashboard-uejez7.streamlit.app/)

This project demonstrates a complete end-to-end analytics platform for an Affiliate Commerce business. It ingests campaign traffic data, calculates critical financial KPIs (ROI, EPC, AOV), and presents actionable insights via an interactive dashboard.

## 🚀 Key Features

- **Automated Data Pipeline**: Ingests raw click data (`.csv`), normalizes it into a specific schema, and persists it in SQLite.
- **Advanced KPI Engine**: Calculates complex metrics:
    - **ROI** (Return on Investment)
    - **EPC** (Earnings Per Click)
    - **AOV** (Average Order Value)
    - **CTR** (Click-Through Rate)
- **Data Quality Monitoring**: Automated checks for anomalies (e.g., Clicks > Impressions, Negative Revenue).
- **Interactive Dashboard**: Built with **Streamlit** & **Plotly**, featuring:
    - Executive Summary with trend lines.
    - Partner Performance Leaderboards.
    - Campaign A/B Test Analysis.
    - Automated "Agent" Recommendations (identifying underperformers).

## 🛠 Tech Stack

- **Python 3.11+**
- **Streamlit**: Interactive Web App
- **Pandas/NumPy**: Data Processing & Arrays
- **SQLite**: Relational Database
- **Plotly Express**: Interactive Visualizations

## 📂 Structure

```
├── data/
│   └── affiliate_commerce.db  # Generated Database
├── dataset/
│   └── amazon_affiliate_clicks.csv # Source Data
├── src/
│   ├── data_ingestion.py      # ETL Pipeline (Agent 1)
│   ├── analytics.py           # KPI Engine & DQ (Agent 2)
│   └── dashboard.py           # UI & Reporting (Agent 3 & 4)
├── requirements.txt
└── README.md
```

## ⚡ Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Data Pipeline** (Ingest CSV -> DB):
   ```bash
   python src/data_ingestion.py
   ```

3. **Launch Dashboard**:
   ```bash
   streamlit run src/dashboard.py
   ```

## 📈 Business Narrative

As a Commerce Data Analyst, the goal is to optimize the "Yield" of every click. This platform helps the team identify:
1. **High-ROI Partners**: Who should we scale? (e.g., Partners with ROI > 4.0)
2. **Efficiency Gaps**: Which partners have volume but low conversion?
3. **Data Integrity**: ensuring our financial reporting is accurate by flagging anomalies immediately.

---
*Built for the New York Post Commerce Data Analyst Role Application.*
