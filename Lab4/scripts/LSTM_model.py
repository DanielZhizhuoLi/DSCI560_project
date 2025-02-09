import pymysql
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error



DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()

query = "SELECT * FROM processed_stock_data;"
df = pd.read_sql_query(query, conn)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values(by=["stock", "datetime"]).reset_index(drop=True)

# price difference percentage**
df["price_diff_pct"] = df.groupby("stock")["close"].pct_change().shift(-1) * 100
df["price_diff_pct"].fillna(0, inplace=True)


features = ["daily_return", "SMA_10", "EMA_10", "volatility", "RSI"]
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df[features])

def create_sequences(data, target, time_steps=60):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps])
        y.append(target[i+time_steps])
    return np.array(X), np.array(y)

X, y = create_sequences(df_scaled, df["price_diff_pct"].values, time_steps=60)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
    LSTM(50),
    Dense(1)  # predict price_diff_pct
])

model.compile(loss="mse", optimizer=tf.keras.optimizers.Adam(learning_rate=0.001))

model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=1, validation_data=(X_test, y_test))

y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Test MSE: {mse:.4f}")


predicted_diff_pct = model.predict(X)


df["predicted_diff_pct"] = np.nan
df.loc[df.index[-len(predicted_diff_pct):], "predicted_diff_pct"] = predicted_diff_pct.flatten()

def calculate_trade_percentage(predicted_value):
    if predicted_value > 1.0:  # 预计上涨超过 1%
        return round(min(predicted_value / 10, 1.0), 2)  # 最大买入 100%
    elif predicted_value < -1.0:  # 预计下跌超过 1%
        return round(max(predicted_value / 10, -1.0), 2)  # 最大卖出 100%
    else:
        return 0  # 变化不大，保持仓位

df["trade_percentage"] = df["predicted_diff_pct"].apply(calculate_trade_percentage)

# **Step 11.1: 计算最终交易信号**
def generate_signal(trade_pct):
    if trade_pct > 0:
        return f"BUY {trade_pct * 100:.0f}%"
    elif trade_pct < 0:
        return f"SELL {-trade_pct * 100:.0f}%"
    else:
        return "HOLD"

df["signal"] = df["trade_percentage"].apply(generate_signal)



cursor.execute("""
    CREATE TABLE IF NOT EXISTS predicted_stock_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock VARCHAR(20) NOT NULL,
        datetime DATETIME NOT NULL,
        close DECIMAL(10,2) NOT NULL,
        predicted_diff_pct DECIMAL(10,6),
        trade_percentage DECIMAL(10,6),
        signal VARCHAR(20)
    );
""")


insert_query = """
    INSERT INTO predicted_stock_data (stock, datetime, close, predicted_diff_pct, trade_percentage, signal)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

values_list = [
    (row["stock"], row["datetime"], row["close"], row["predicted_diff_pct"], row["trade_percentage"], row["signal"])
    for _, row in df.iterrows() if not pd.isna(row["predicted_diff_pct"])
]

cursor.executemany(insert_query, values_list)
conn.commit()


cursor.close()
conn.close()
