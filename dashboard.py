import os, sys, yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# Support both local .env and Streamlit Cloud secrets
if not os.getenv("OPENAI_API_KEY"):
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── paths ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

AGENTS_YAML = BASE / "src/stock_crew/config/agents.yaml"
TASKS_YAML  = BASE / "src/stock_crew/config/tasks.yaml"

# ── page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analysis Crew",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Stock Analysis Crew Dashboard")

# ── sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    raw_tickers = st.text_input(
        "Tickers (comma-separated)",
        value="AAPL, NVDA",
        help="e.g. AAPL, TSLA, MSFT",
    )
    period = st.selectbox("History period", ["1mo", "3mo", "6mo", "1y"], index=0)

    st.divider()
    st.header("AI Analysis")
    ai_ticker = st.selectbox(
        "Ticker for AI crew",
        options=[t.strip().upper() for t in raw_tickers.split(",") if t.strip()],
    )
    run_crew_btn = st.button("🤖 Run Crew Analysis", type="primary")
    st.caption("Crew runs take ~60 seconds")

tickers = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

# ── fetch market data ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_info(ticker: str) -> dict:
    info = yf.Ticker(ticker).info
    return {
        "ticker":       ticker,
        "price":        info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
        "change_5d":    _five_day_change(ticker),
        "volume":       info.get("volume", "N/A"),
        "market_cap":   info.get("marketCap", "N/A"),
        "sector":       info.get("sector", "N/A"),
        "pe_ratio":     info.get("trailingPE", "N/A"),
        "52w_high":     info.get("fiftyTwoWeekHigh", "N/A"),
        "52w_low":      info.get("fiftyTwoWeekLow", "N/A"),
    }

@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period)

def _five_day_change(ticker: str) -> float | str:
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if len(hist) >= 2:
            return round((hist["Close"].iloc[-1] - hist["Close"].iloc[0])
                         / hist["Close"].iloc[0] * 100, 2)
    except Exception:
        pass
    return "N/A"

def fmt_large(n):
    if isinstance(n, (int, float)):
        if n >= 1e12: return f"${n/1e12:.2f}T"
        if n >= 1e9:  return f"${n/1e9:.2f}B"
        if n >= 1e6:  return f"${n/1e6:.2f}M"
        return f"${n:,.0f}"
    return str(n)

# ── tabs ───────────────────────────────────────────────────────────────────
tab_metrics, tab_charts, tab_compare, tab_ai = st.tabs(
    ["📊 Metrics", "📉 Price History", "⚖️ Compare", "🤖 AI Analysis"]
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — Metrics cards
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_metrics:
    if not tickers:
        st.warning("Enter at least one ticker in the sidebar.")
    else:
        with st.spinner("Fetching market data…"):
            all_info = {t: fetch_info(t) for t in tickers}

        for ticker, info in all_info.items():
            st.subheader(ticker)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            price = info["price"]
            chg   = info["change_5d"]
            chg_str   = f"{chg}%" if isinstance(chg, float) else str(chg)
            chg_delta = chg_str if isinstance(chg, float) else None

            c1.metric("Price",        f"${price}" if isinstance(price, (int, float)) else price)
            c2.metric("5-Day Change", chg_str, delta=chg_delta)
            c3.metric("Volume",       fmt_large(info["volume"]).replace("$", ""))
            c4.metric("Market Cap",   fmt_large(info["market_cap"]))
            c5.metric("P/E Ratio",    f"{info['pe_ratio']:.1f}" if isinstance(info["pe_ratio"], float) else str(info["pe_ratio"]))
            c6.metric("Sector",       info["sector"])

            r1, r2 = st.columns(2)
            r1.metric("52-Week High", f"${info['52w_high']}" if isinstance(info['52w_high'], (int,float)) else info['52w_high'])
            r2.metric("52-Week Low",  f"${info['52w_low']}"  if isinstance(info['52w_low'],  (int,float)) else info['52w_low'])
            st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — Price history charts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_charts:
    if not tickers:
        st.warning("Enter at least one ticker in the sidebar.")
    else:
        for ticker in tickers:
            with st.spinner(f"Loading {ticker} history…"):
                hist = fetch_history(ticker, period)

            if hist.empty:
                st.error(f"No data for {ticker}")
                continue

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name=ticker,
            ))
            fig.update_layout(
                title=f"{ticker} — {period} Price History",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                xaxis_rangeslider_visible=False,
                height=420,
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

            vol_fig = px.bar(
                hist.reset_index(), x="Date", y="Volume",
                title=f"{ticker} — Volume",
                template="plotly_dark", height=200,
                color_discrete_sequence=["#636EFA"],
            )
            vol_fig.update_layout(margin=dict(t=30, b=10))
            st.plotly_chart(vol_fig, use_container_width=True)
            st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — Comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_compare:
    if len(tickers) < 2:
        st.info("Enter at least 2 tickers to compare.")
    else:
        with st.spinner("Building comparison…"):
            all_info = {t: fetch_info(t) for t in tickers}

        # Normalised price history overlay
        st.subheader("Normalised Price Performance")
        fig_norm = go.Figure()
        for ticker in tickers:
            hist = fetch_history(ticker, period)
            if not hist.empty:
                norm = hist["Close"] / hist["Close"].iloc[0] * 100
                fig_norm.add_trace(go.Scatter(
                    x=hist.index, y=norm, name=ticker, mode="lines"
                ))
        fig_norm.update_layout(
            yaxis_title="Indexed (base = 100)",
            xaxis_title="Date",
            template="plotly_dark",
            height=380,
        )
        st.plotly_chart(fig_norm, use_container_width=True)

        # Bar chart — market cap
        st.subheader("Market Cap Comparison")
        caps = {t: d["market_cap"] for t, d in all_info.items()
                if isinstance(d["market_cap"], (int, float))}
        if caps:
            fig_cap = px.bar(
                x=list(caps.keys()), y=[v/1e9 for v in caps.values()],
                labels={"x": "Ticker", "y": "Market Cap (B USD)"},
                template="plotly_dark", height=300,
                color=list(caps.keys()),
            )
            st.plotly_chart(fig_cap, use_container_width=True)

        # Side-by-side metrics table
        st.subheader("Metrics Table")
        rows = []
        for t, d in all_info.items():
            rows.append({
                "Ticker":       t,
                "Price":        f"${d['price']}",
                "5-Day %":      f"{d['change_5d']}%",
                "Market Cap":   fmt_large(d["market_cap"]),
                "P/E":          d["pe_ratio"],
                "Sector":       d["sector"],
                "52W High":     f"${d['52w_high']}",
                "52W Low":      f"${d['52w_low']}",
            })
        st.dataframe(pd.DataFrame(rows).set_index("Ticker"), use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — AI Analysis (StockCrew)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab_ai:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not found in environment. Add it to your .env file.")
    else:
        st.info(f"Selected ticker for AI analysis: **{ai_ticker}**. Click **Run Crew Analysis** in the sidebar.")

        if "crew_results" not in st.session_state:
            st.session_state.crew_results = {}

        if run_crew_btn:
            from crewai import Agent, Task, Crew, Process
            from crewai.tools import tool as crewai_tool

            @crewai_tool
            def stock_tool(ticker: str) -> str:
                """Fetch key market data for a given stock ticker using yfinance."""
                try:
                    t = yf.Ticker(ticker)
                    info = t.info
                    price  = info.get("currentPrice", "N/A")
                    volume = info.get("volume", "N/A")
                    mcap   = info.get("marketCap", "N/A")
                    sector = info.get("sector", "N/A")
                    try:
                        hist = t.history(period="5d")
                        pct = round((hist["Close"].iloc[-1] - hist["Close"].iloc[0])
                                    / hist["Close"].iloc[0] * 100, 2) if len(hist) >= 2 else "N/A"
                    except Exception:
                        pct = "N/A"
                    return (f"Ticker: {ticker.upper()}\nCurrent Price: {price}\n"
                            f"5-Day % Change: {pct}%\nVolume: {volume}\n"
                            f"Market Cap: {mcap}\nSector: {sector}")
                except Exception as e:
                    return f"Error fetching data for {ticker}: {e}"

            with open(AGENTS_YAML) as f:
                agents_cfg = yaml.safe_load(f)
            with open(TASKS_YAML) as f:
                tasks_cfg = yaml.safe_load(f)

            with st.spinner(f"Running crew for {ai_ticker}… (~60s)"):
                researcher = Agent(
                    role=agents_cfg["researcher"]["role"],
                    goal=agents_cfg["researcher"]["goal"],
                    backstory=agents_cfg["researcher"]["backstory"],
                    tools=[stock_tool],
                    verbose=False,
                )
                strategist = Agent(
                    role=agents_cfg["strategist"]["role"],
                    goal=agents_cfg["strategist"]["goal"],
                    backstory=agents_cfg["strategist"]["backstory"],
                    verbose=False,
                )
                pitcher = Agent(
                    role=agents_cfg["pitcher"]["role"],
                    goal=agents_cfg["pitcher"]["goal"],
                    backstory=agents_cfg["pitcher"]["backstory"],
                    verbose=False,
                )
                research_task = Task(
                    description=tasks_cfg["research_task"]["description"],
                    expected_output=tasks_cfg["research_task"]["expected_output"],
                    agent=researcher,
                )
                strategy_task = Task(
                    description=tasks_cfg["strategy_task"]["description"],
                    expected_output=tasks_cfg["strategy_task"]["expected_output"],
                    agent=strategist,
                )
                pitch_task = Task(
                    description=tasks_cfg["pitch_task"]["description"],
                    expected_output=tasks_cfg["pitch_task"]["expected_output"],
                    agent=pitcher,
                )
                crew = Crew(
                    agents=[researcher, strategist, pitcher],
                    tasks=[research_task, strategy_task, pitch_task],
                    process=Process.sequential,
                    verbose=False,
                )
                result = crew.kickoff(inputs={"ticker": ai_ticker})

            # store task outputs individually
            st.session_state.crew_results[ai_ticker] = {
                "research":  str(research_task.output),
                "strategy":  str(strategy_task.output),
                "pitch":     str(pitch_task.output),
            }
            st.success(f"Analysis for {ai_ticker} complete!")

        # display cached results
        if st.session_state.crew_results:
            for ticker, res in st.session_state.crew_results.items():
                st.subheader(f"Analysis — {ticker}")

                col_l, col_r = st.columns(2)
                with col_l:
                    with st.expander("🔍 Research Data", expanded=True):
                        st.text(res["research"])
                    with st.expander("📋 Strategy (Bull/Bear)", expanded=True):
                        st.markdown(res["strategy"])
                with col_r:
                    with st.expander("📝 Investment Pitch", expanded=True):
                        st.markdown(res["pitch"])
                st.divider()
        else:
            st.markdown("_No analysis yet. Select a ticker and click **Run Crew Analysis**._")
