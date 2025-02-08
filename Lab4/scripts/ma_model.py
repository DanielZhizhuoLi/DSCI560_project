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
	WHERE stock = 'AAPL'
	"""
AAPL = pd.read_sql(query, engine)
AAPL["SMA_10"] = AAPL['close'].rolling(window = 10).mean()
AAPL["SMA_20"] = AAPL['close'].rolling(window = 20).mean()
AAPL["RSI_7"] = ta.rsi(AAPL['close'], length=7)
AAPL["RSI_14"] = ta.rsi(AAPL['close'], length=14)
AAPL["daily_return"] = AAPL['close'].pct_change()
AAPL['first_difference'] = AAPL['close'].diff()
AAPL['close_log'] = np.log(AAPL['close'])
AAPL['datetime'] = pd.to_datetime(AAPL['datetime']) 
AAPL.set_index('datetime', inplace= True)
AAPL.dropna(inplace= True)

# need to remove the trends and seasonality before plotting acf
#plot_acf(AAPL['first_difference'], lags=20)
#plt.savefig("../data/acf.png")

# 2/3 of training and 1/3 of testing
train_size = int(len(AAPL) * 0.66)
train, test = AAPL['close_log'][:train_size], AAPL['close_log'][train_size:]
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
plt.savefig("../data/ma_model.png")

print("plots are saved")
plt.close()


# evaluate the model
rmse = np.sqrt(mean_squared_error(actual_test_price, predicted_price))
print(f"RMSE: {rmse}")

# strategy: if daily return > 0 buy else hold
s_data = pd.concat([actual_test_price, predicted_price], axis = 1)
s_data.columns = ["actual", "predicted"] 
s_data["actual_return"] = s_data['actual'].pct_change()
s_data["predict_return"] = s_data["predicted"].pct_change()
s_data["signal"] = np.where(s_data["predict_return"] > 0, 1, 0)
s_return = ((1 + s_data["actual_return"]) * s_data["signal"].shift(1)).cumprod().iloc[-1]
m_return = (1+ s_data["actual_return"]).cumprod().iloc[-1]

print(f"s_return: {s_return}")
print(f"m_return: {m_return}")

