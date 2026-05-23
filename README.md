# Stock Analysis Crew Dashboard

A multi-agent AI stock analysis dashboard built with Streamlit, powered by a Researcher → Strategist → Pitcher pipeline.

## Live Demo

[stock-analysis-crew-ucdxbuzgbzuwyvxa5nsmapp.streamlit.app](https://stock-analysis-crew-ucdxbuzgbzuwyvxa5nsmapp.streamlit.app/)

## Features

| Tab | Description |
|-----|-------------|
| 📊 Metrics | Live price, 5-day change, market cap, P/E, 52W high/low |
| 📉 Price History | Candlestick chart + volume bars (1mo / 3mo / 6mo / 1y) |
| ⚖️ Compare | Normalised performance overlay + side-by-side metrics table |
| 🤖 AI Analysis | 3-agent pipeline: Researcher → Strategist → Pitcher |

## AI Pipeline

1. **Researcher** — fetches live market data via yfinance
2. **Strategist** — produces a Bull/Bear label + Buy/Hold/Sell recommendation with 3 supporting reasons
3. **Pitcher** — writes a structured markdown investment pitch (under 300 words)

## Run Locally

```bash
git clone https://github.com/razkatinka/stock-analysis-crew.git
cd stock-analysis-crew
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENAI_API_KEY=your_key_here
```

Then run:
```bash
streamlit run dashboard.py
```

## Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub
3. Set `dashboard.py` as the main file
4. Add your `OPENAI_API_KEY` under **Settings → Secrets**:
```toml
OPENAI_API_KEY = "your_key_here"
```

## Tech Stack

- [Streamlit](https://streamlit.io) — dashboard framework
- [yfinance](https://github.com/ranaroussi/yfinance) — market data
- [Plotly](https://plotly.com) — interactive charts
- [OpenAI](https://openai.com) — AI analysis (gpt-4o-mini)
