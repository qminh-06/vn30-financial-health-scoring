"""Technical Analysis (TA) Module for VCB.

Tính toán các chỉ báo kỹ thuật cốt lõi từ dữ liệu OHLCV:
1. Đường xu hướng (Trend): SMA20, SMA50, SMA200, EMA20.
2. Động lượng & Quá mua/Quá bán (Momentum): RSI (14).
3. Xu hướng phân kỳ (Trend Convergence/Divergence): MACD, Signal line, MACD Histogram.
4. Mức hỗ trợ & Kháng cự ngắn/trung hạn.
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def compute_ta_indicators(df_price: pd.DataFrame) -> pd.DataFrame:
    """df_price: DataFrame chứa các cột ['time', 'open', 'high', 'low', 'close', 'volume']."""
    df = df_price.copy()
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)

    close = df["close"]

    # 1. Moving Averages
    df["SMA20"] = close.rolling(window=20).mean()
    df["SMA50"] = close.rolling(window=50).mean()
    df["SMA200"] = close.rolling(window=200).mean()
    df["EMA20"] = close.ewm(span=20, adjust=False).mean()

    # 2. RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    # 3. MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    return df


def get_latest_ta_signals(df_indicators: pd.DataFrame) -> Dict[str, Any]:
    """Trích xuất tín hiệu kỹ thuật tại phiên giao dịch mới nhất (hoặc mốc 01/01/2026)."""
    latest = df_indicators.iloc[-1]
    prev = df_indicators.iloc[-2] if len(df_indicators) > 1 else latest

    close = float(latest["close"])
    sma20 = float(latest["SMA20"]) if not pd.isna(latest["SMA20"]) else None
    sma50 = float(latest["SMA50"]) if not pd.isna(latest["SMA50"]) else None
    sma200 = float(latest["SMA200"]) if not pd.isna(latest["SMA200"]) else None
    rsi = float(latest["RSI14"]) if not pd.isna(latest["RSI14"]) else 50.0
    macd = float(latest["MACD"]) if not pd.isna(latest["MACD"]) else 0.0
    macd_signal = float(latest["MACD_SIGNAL"]) if not pd.isna(latest["MACD_SIGNAL"]) else 0.0

    # Đánh giá xu hướng
    trend = "Sideway"
    if sma50 and sma200:
        if close > sma50 > sma200:
            trend = "Uptrend mạnh (Trên SMA50 & SMA200)"
        elif close > sma200:
            trend = "Uptrend trung - dài hạn"
        elif close < sma50 < sma200:
            trend = "Downtrend"

    # Trạng thái RSI
    rsi_status = "Trung lập"
    if rsi >= 70:
        rsi_status = "Quá mua (Overbought - Khả năng rung lắc chốt lời)"
    elif rsi <= 30:
        rsi_status = "Quá bán (Oversold - Vùng tiềm năng hồi phục)"

    # Tín hiệu MACD
    macd_signal_status = "Tích cực" if macd > macd_signal else "Tiêu cực"

    return {
        "latest_date": str(latest.get("time", "N/A")),
        "close_price": close,
        "trend_status": trend,
        "RSI": round(rsi, 1),
        "RSI_status": rsi_status,
        "MACD_status": macd_signal_status,
        "SMA20": round(sma20, 0) if sma20 else None,
        "SMA50": round(sma50, 0) if sma50 else None,
        "SMA200": round(sma200, 0) if sma200 else None,
    }
