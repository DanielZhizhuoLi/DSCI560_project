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
	WHERE stock = ' TSLA'
	"""
# add more features 
TSLA = pd.read_sql(query, engine)
TSLA["SMA_10"] = TSLA['close'].rolling(window = 10).mean()
TSLA["SMA_20"] = TSLA['close'].rolling(window = 20).mean()
TSLA["RSI_7"] = ta.rsi(TSLA['close'], length=7)
TSLA["RSI_14"] = ta.rsi(TSLA['close'], length=14)
TSLA["daily_return"] = TSLA['close'].pct_change()
TSLA['first_difference'] = TSLA['close'].diff()
TSLA['close_log'] = np.log(TSLA['close'])
TSLA['datetime'] = pd.to_datetime(TSLA['datetime']) 
TSLA.set_index('datetime', inplace= True)
TSLA.dropna(inplace= True)

# need to remove the trends and seasonality before plotting acf
#plot_acf(TSLA['close_log'], lags=20)
#plt.savefig("../data/TSLA/TSLA_acf.png")

# 2/3 of training and 1/3 of testing
train_size = int(len(TSLA) * 0.66)
train, test = TSLA['close_log'][:train_size], TSLA['close_log'][train_size:]
train = train.asfreq('h').ffill()
test = test.asfreq('h').ffill()

# ma is univariate model so only one variable input
ma = ARIMA(train, order= (2, 0, 1) )
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
plt.savefig("../data/TSLA/ma_model.png")
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
print(f"s_return on TSLA: {s_return}", "%")
print(f"m_return on TSLA: {m_return}", "%")


