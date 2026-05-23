from crewai.tools import tool
import yfinance as yf


@tool
def stock_tool(ticker: str) -> str:
    """Fetch key market data for a given stock ticker using yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info

        current_price = info.get("currentPrice", "N/A")
        volume = info.get("volume", "N/A")
        market_cap = info.get("marketCap", "N/A")
        sector = info.get("sector", "N/A")

        try:
            hist = t.history(period="5d")
            if len(hist) >= 2:
                oldest = hist["Close"].iloc[0]
                latest = hist["Close"].iloc[-1]
                five_day_pct = round((latest - oldest) / oldest * 100, 2)
            else:
                five_day_pct = "N/A"
        except Exception:
            five_day_pct = "N/A"

        return (
            f"Ticker: {ticker.upper()}\n"
            f"Current Price: {current_price}\n"
            f"5-Day % Change: {five_day_pct}%\n"
            f"Volume: {volume}\n"
            f"Market Cap: {market_cap}\n"
            f"Sector: {sector}"
        )
    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"
