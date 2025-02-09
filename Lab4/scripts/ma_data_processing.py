import numpy as np
import pandas as pd
import pandas_ta as ta
import pymysql
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "stock"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
query ="""
	SELECT * 
	FROM  stock_data
	WHERE stock = ' LCID'
	"""
df = pd.read_sql(query, engine)
df["SMA_10"] = df['close'].rolling(window = 10).mean()
df["SMA_20"] = df['close'].rolling(window = 20).mean()
df["RSI_7"] = ta.rsi(df['close'], length=7)
df["RSI_14"] = ta.rsi(df['close'], length=14)
df["daily_return"] = df['close'].pct_change()

df.dropna(inplace= True)

df["label"] = np.where( (df["SMA_10"] > df["SMA_20"]) & (df["SMA_10"].shift(1) < df["SMA_20"].shift(1)), 1, 0)
df["signal"] = df["label"].replace(0, np.nan).ffill()
df["s_return"] = df["daily_return"] * df["signal"].shift(1)
df["singal"] = df["signal"].fillna(0)

m_return = (1 + df["daily_return"]).cumprod()
s_return = (1 +df["s_return"]).cumprod()
print("market return: ", round((m_return.iloc[-1] -1) * 100, 2), '%')
print("strategy return: ", round((s_return.iloc[-1] -1) * 100, 2), '%')

# plot LCID stock graph
fig, ax = plt.subplots(2, 1, figsize = (10, 8), sharex = True)

ax[0].plot(df['close'], label='Close Price', color='blue', linewidth=2)
ax[0].plot(df['SMA_10'], label='SMA(10)', color='red', linestyle='--')
ax[0].plot(df['SMA_20'], label='SMA(20)', color='green', linestyle='--')
ax[0].set_title("LCID Price and Moving Average")
ax[0].set_ylabel("Price")
ax[0].legend(loc='best')

ax[1].plot(df['RSI_7'], label='RSI(7)', color='purple', linewidth=2)
ax[1].plot(df['RSI_14'], label='RSI(14)', color='orange', linewidth=2)
ax[1].axhline(70, color='red', linestyle ='--')
ax[1].axhline(30, color='green', linestyle='--')
ax[1].set_title("RSI")
ax[1].set_ylabel("RSI")
ax[1].legend(loc='best')

plt.xlabel('Date')
plt.tight_layout()
plt.savefig("../data/LCID/plot.png")
#print("plot is saved")

plt.close()
