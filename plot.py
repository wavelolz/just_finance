#%%
import time
import numpy as np
import pandas as pd
import ta
import mplfinance as mpf


#%%
data = pd.read_csv("testingData.csv")

plot_data = data[["date", "Trading_Volume", "open", "close", "max", "min"]]
plot_data.columns = ["Date", "Volume", "Open", "Close", "High", "Low"]
plot_data.index = pd.to_datetime(plot_data["Date"])
plot_data = plot_data.drop(["Date"], axis=1)
plot_data = plot_data[["Open", "High", "Low", "Close", "Volume"]]

ema10 = ta.trend.EMAIndicator(plot_data["Close"], 10, False).ema_indicator()
ema20 = ta.trend.EMAIndicator(plot_data["Close"], 20, False).ema_indicator()
addplot_ema10 = mpf.make_addplot(ema10, color="r")
addplot_ema20 = mpf.make_addplot(ema20, color="g")
mc = mpf.make_marketcolors(up="r", down="g")
s = mpf.make_mpf_style(marketcolors=mc)
fig, ax = mpf.plot(
    plot_data, 
    type="candle", 
    volume=True, 
    style=s, 
    addplot=[addplot_ema10, addplot_ema20],
    returnfig = True
    )

ax[0].legend([0]*4)
handles = ax[0].get_legend().legendHandles
ax[0].legend(handles = handles[2:], labels = ["EMA10", "EMA20"])