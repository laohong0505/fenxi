import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import pandas as pd
import datetime
import threading

# ===== 数据源配置 =====
EXCHANGES = [
    {"name": "binance", "url": "https://api.binance.com/api/v3/klines", "symbol_format": lambda s: s.upper()},
    {"name": "kucoin", "url": "https://api.kucoin.com/api/v1/market/candles", "symbol_format": lambda s: s.replace("/", "-")}
]

# ===== 获取K线数据 =====
def fetch_kline(symbol, interval="12h", limit=200):
    for ex in EXCHANGES:
        try:
            if ex["name"] == "binance":
                params = {"symbol": ex["symbol_format"](symbol), "interval": interval, "limit": limit}
                response = requests.get(ex["url"], params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data, columns=["open_time", "open", "high", "low", "close", "volume",
                                                     "close_time", "quote_asset_volume", "trades",
                                                     "taker_base", "taker_quote", "ignore"])
                    df["close"] = df["close"].astype(float)
                    return df
            elif ex["name"] == "kucoin":
                params = {"symbol": ex["symbol_format"](symbol), "type": interval}
                response = requests.get(ex["url"], params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                if "data" in data:
                    df = pd.DataFrame(data["data"], columns=["time", "open", "close", "high", "low", "volume"])
                    df["close"] = df["close"].astype(float)
                    return df
        except Exception:
            continue
    return None

# ===== 计算指标 =====
def analyze_symbol(symbol, interval):
    df = fetch_kline(symbol, interval)
    if df is None:
        return f"{symbol}: 数据获取失败，请检查交易所或币种。"

    close_prices = df["close"].astype(float)
    ma5 = close_prices.rolling(window=5).mean().iloc[-1]
    ma10 = close_prices.rolling(window=10).mean().iloc[-1]
    ma20 = close_prices.rolling(window=20).mean().iloc[-1]
    ma120 = close_prices.rolling(window=120).mean().iloc[-1]

    # 风险判断
    volatility = (close_prices.max() - close_prices.min()) / close_prices.mean()
    if volatility > 0.15:
        risk = "高"
        risk_color = "red"
    elif volatility > 0.08:
        risk = "中"
        risk_color = "orange"
    else:
        risk = "低"
        risk_color = "green"

    current_price = close_prices.iloc[-1]
    result = f"""
币种: {symbol.upper()}
当前价格: {current_price:.4f} USDT
MA5={ma5:.4f} MA10={ma10:.4f} MA20={ma20:.4f} MA120={ma120:.4f}
波动率: {volatility:.2%}
风险等级: {risk}
"""
    return result, risk_color

# ===== 批量分析 =====
def analyze_multiple(symbols, interval):
    results = []
    for sym in symbols:
        sym = sym.strip()
        if sym:
            res, color = analyze_symbol(sym, interval)
            results.append((res, color))
    return results

# ===== GUI 界面 =====
def start_analysis():
    symbols = entry_symbol.get("1.0", "end").strip().split(",")
    interval = combo_interval.get()
    text_output.delete("1.0", tk.END)

    def run():
        results = analyze_multiple(symbols, interval)
        for res, color in results:
            text_output.insert(tk.END, res + "\n" + "="*50 + "\n", color)

    threading.Thread(target=run).start()

# ===== 主界面 =====
root = tk.Tk()
root.title("Crypto 多币种分析工具")
root.geometry("900x700")
root.configure(bg="#1e1e1e")

# 样式
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Microsoft YaHei", 11))
style.configure("TButton", font=("Microsoft YaHei", 11), padding=6)
style.configure("TCombobox", font=("Microsoft YaHei", 11))

# 布局
frame_top = ttk.Frame(root)
frame_top.pack(pady=10)

ttk.Label(frame_top, text="输入币种（逗号分隔）:").grid(row=0, column=0, padx=5)
entry_symbol = tk.Text(frame_top, width=50, height=2, font=("Microsoft YaHei", 11))
entry_symbol.grid(row=0, column=1, padx=5)

ttk.Label(frame_top, text="周期:").grid(row=0, column=2, padx=5)
combo_interval = ttk.Combobox(frame_top, values=["1h", "4h", "12h", "1d"], width=10)
combo_interval.set("12h")
combo_interval.grid(row=0, column=3, padx=5)

btn_analyze = ttk.Button(frame_top, text="开始分析", command=start_analysis)
btn_analyze.grid(row=0, column=4, padx=10)

btn_refresh = ttk.Button(frame_top, text="刷新行情", command=start_analysis)
btn_refresh.grid(row=0, column=5, padx=10)

# 输出框
text_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=110, height=30, font=("Consolas", 10), bg="#252526", fg="white")
text_output.pack(pady=10)

# 风险颜色标签
text_output.tag_config("red", foreground="red")
text_output.tag_config("orange", foreground="orange")
text_output.tag_config("green", foreground="green")

root.mainloop()
