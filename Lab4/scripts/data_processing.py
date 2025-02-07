import numpy as np
import pandas as pd
import pandas_ta as ta
import pymysql
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "stock"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
query ="""
	SELECT * 
	FROM  stock_data
	WHERE stock = 'AAPL'
	"""
AAPL = pd.read_sql(query, engine)
AAPL["SMA_10"] = AAPL['close'].rolling(window = 10).mean()
AAPL["SMA_20"] = AAPL['close'].rolling(window = 20).mean()
AAPL["RSI_7"] = ta.rsi(AAPL['close'], length=7)
AAPL["RSI_14"] = ta.rsi(AAPL['close'], length=14)
AAPL["daily_return"] = AAPL['close'].pct_change()

AAPL.dropna(inplace= True)

AAPL["label"] = np.where( (AAPL["SMA_10"] > AAPL["SMA_20"]) & (AAPL["SMA_10"].shift(1) < AAPL["SMA_20"].shift(1)), 1, 0)
AAPL["signal"] = AAPL["label"].replace(0, np.nan).ffill()
AAPL["s_return"] = AAPL["daily_return"] * AAPL["signal"].shift(1)
AAPL["singal"] = AAPL["signal"].fillna(0)

m_return = (1 + AAPL["daily_return"]).cumprod()
s_return = (1 +AAPL["s_return"]).cumprod()
print("market return: ", round((m_return.iloc[-1] -1) * 100, 2), '%')
print("strategy return: ", round((s_return.iloc[-1] -1) * 100, 2), '%')

# plot AAPL stock graph
fig, ax = plt.subplots(2, 1, figsize = (10, 8), sharex = True)

ax[0].plot(AAPL['close'], label='Close Price', color='blue', linewidth=2)
ax[0].plot(AAPL['SMA_10'], label='SMA(10)', color='red', linestyle='--')
ax[0].plot(AAPL['SMA_20'], label='SMA(20)', color='green', linestyle='--')
ax[0].set_title("AAPL Price and Moving Average")
ax[0].set_ylabel("Price")
ax[0].legend(loc='best')

ax[1].plot(AAPL['RSI_7'], label='RSI(7)', color='purple', linewidth=2)
ax[1].plot(AAPL['RSI_14'], label='RSI(14)', color='orange', linewidth=2)
ax[1].axhline(70, color='red', linestyle ='--')
ax[1].axhline(30, color='green', linestyle='--')
ax[1].set_title("RSI")
ax[1].set_ylabel("RSI")
ax[1].legend(loc='best')

plt.xlabel('Date')
plt.tight_layout()
#plt.savefig("../data/plot.png")
#print("plot is saved")
plt.close()

#

