#%%
import time
import numpy as np
import pandas as pd
import ta
import plotly.graph_objects as go


#%%
data = pd.read_csv("testingData.csv")

plot_data = data[["date", "Trading_Volume", "open", "close", "max", "min"]]
plot_data.columns = ["Date", "Volume", "Open", "Close", "High", "Low"]
plot_data["EMA5"] = ta.trend.EMAIndicator(plot_data["Close"], 5, False).ema_indicator()
plot_data["EMA10"] = ta.trend.EMAIndicator(plot_data["Close"], 10, False).ema_indicator()
plot_data["EMA20"] = ta.trend.EMAIndicator(plot_data["Close"], 20, False).ema_indicator()
fig = go.Figure(
    data=[
        go.Candlestick(x=plot_data["Date"],
                       open=plot_data["Open"],
                       high=plot_data["High"],
                       low=plot_data["Low"],
                       close=plot_data["Close"])
    ]
)
fig.add_trace(
    go.Scatter(
        x=plot_data["Date"],
        y=plot_data["EMA5"],
        mode="lines",
        name="EMA5"
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_data["Date"],
        y=plot_data["EMA10"],
        mode="lines",
        name="EMA10"
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_data["Date"],
        y=plot_data["EMA20"],
        mode="lines",
        name="EMA20"
    )
)
fig.update_layout(xaxis_rangeslider_visible=False,  # Hides the range slider
                  title='Interactive Candlestick Chart')