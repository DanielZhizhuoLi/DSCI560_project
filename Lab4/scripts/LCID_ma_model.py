import numpy as np
import pandas as pd
import pandas_ta as ta
import pymysql
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf
from sklearn.metrics import mean_squared_error

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
# add more features 
df = pd.read_sql(query, engine)
df["SMA_10"] = df['close'].rolling(window = 10).mean()
df["SMA_20"] = df['close'].rolling(window = 20).mean()
df["RSI_7"] = ta.rsi(df['close'], length=7)
df["RSI_14"] = ta.rsi(df['close'], length=14)
df["daily_return"] = df['close'].pct_change()
df['first_difference'] = df['close'].diff()
df['close_log'] = np.log(df['close'])
df['datetime'] = pd.to_datetime(df['datetime']) 
df.set_index('datetime', inplace= True)
df.dropna(inplace= True)

# need to remove the trends and seasonality before plotting acf
#plot_acf(df['close_log'], lags=20)
#plt.savefig("../data/LCID/LCID_acf.png")

# 2/3 of training and 1/3 of testing
train_size = int(len(df) * 0.66)
train, test = df['close_log'][:train_size], df['close_log'][train_size:]
train = train.asfreq('h').ffill()
test = test.asfreq('h').ffill()

# ma is univariate model so only one variable input
ma = ARIMA(train, order= (1, 0, 1) )
results = ma.fit()
forecast = results.forecast(steps = len(test))


forecast = pd.Series(forecast, index=test.index)
forecast = forecast.ffill()
predicted_price = np.exp(forecast)
actual_test_price = np.exp(test)
actual_train_price = np.exp(train)
plt.plot(train.index, actual_train_price)
plt.plot(test.index, actual_test_price, label='Actual price', color='orange')
plt.plot(test.index, predicted_price, label='Predicted price', color='red')
plt.legend()
plt.savefig("../data/LCID/ma_model.png")
plt.close()


# evaluate the model
rmse = np.sqrt(mean_squared_error(actual_test_price, predicted_price))


# strategy: if daily return > 0 buy else hold
s_data = pd.concat([actual_test_price, predicted_price], axis = 1)
s_data.columns = ["actual", "predicted"] 
s_data["actual_return"] = s_data['actual'].pct_change()
s_data["predict_return"] = s_data["predicted"].pct_change()
s_data["signal"] = np.where(s_data["predict_return"] > 0, 1, 0)
s_data["strategy_return"] = np.where(s_data["signal"].shift(1) == 1, s_data["actual_return"], 0)
s_data["cumulative_strategy_return"] = (1 + s_data["strategy_return"]).cumprod() -1
s_data["cumulative_market_return"] = (1 + s_data["actual_return"]).cumprod() -1

s_return = s_data["cumulative_strategy_return"].iloc[-1] * 100
m_return = s_data["cumulative_market_return"].iloc[-1] * 100

print(f"RMSE: {rmse}")
print(f"s_return on LCID: {s_return}", "%")
print(f"m_return on LCID: {m_return}", "%")


