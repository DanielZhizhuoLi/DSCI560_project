import pymysql
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import sys

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()
print("Connected to MySQL.")

query = "SELECT * FROM processed_stock_data;"
df = pd.read_sql_query(query, conn)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values(by=["stock", "datetime"]).reset_index(drop=True)

df["price_diff_pct"] = df.groupby("stock")["close"].pct_change().shift(-1) * 100
df["price_diff_pct"].fillna(0, inplace=True)


features = ["daily_return", "SMA_10", "EMA_10", "volatility", "RSI"]


scaler = MinMaxScaler()


train_data, test_data = train_test_split(df, test_size=0.2, shuffle=False, random_state=42)


scaler.fit(train_data[features])

# Transform both train and test sets separately
df.loc[train_data.index, features] = scaler.transform(train_data[features])
df.loc[test_data.index, features] = scaler.transform(test_data[features])


def create_sequences(data, target, time_steps=30):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps])
        y.append(target[i+time_steps])
    return np.array(X), np.array(y)

X, y = create_sequences(df[features].values, df["price_diff_pct"].values, time_steps=30)


print(f"Data Shape - X: {X.shape}, y: {y.shape}")
if X.shape[0] == 0 or y.shape[0] == 0:
    print("ERROR: X or y is empty. Check dataset preprocessing.")
    sys.exit()


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)


model = Sequential([
    Bidirectional(LSTM(64, return_sequences=True, input_shape=(X.shape[1], X.shape[2]))),
    BatchNormalization(),
    Dropout(0.2),
    Bidirectional(LSTM(64)),
    BatchNormalization(),
    Dropout(0.2),
    Dense(1)  # Predict price_diff_pct
])

model.compile(loss="mse", optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001))


print("Training the model...")
history = model.fit(
    X_train, y_train,
    epochs=30, batch_size=32, verbose=1,
    validation_data=(X_test, y_test)
)
print("Model Training Completed.")


train_loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(10, 5))
plt.plot(train_loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.xlabel("Epochs")
plt.ylabel("Loss (MSE)")
plt.title("Training vs Validation Loss")
plt.legend()
plt.grid()
plt.show()


print("Evaluating model...")
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

train_mse = mean_squared_error(y_train, y_train_pred)
test_mse = mean_squared_error(y_test, y_test_pred)

print(f"Final Training MSE: {train_mse:.4f}")
print(f"Final Test MSE: {test_mse:.4f}")


print("Generating predictions...")
predicted_diff_pct = model.predict(X)
df["predicted_diff_pct"] = np.nan
df.loc[df.index[-len(predicted_diff_pct):], "predicted_diff_pct"] = predicted_diff_pct.flatten()
print("Predictions Completed.")


THRESHOLD = 2 * 0.036

def calculate_trade_percentage(predicted_value):
    if predicted_value > THRESHOLD:
        return round(min(predicted_value / 5, 1.0), 2)
    elif predicted_value < -THRESHOLD:
        return round(max(predicted_value / 5, -1.0), 2)
    else:
        return 0

df["trade_percentage"] = df["predicted_diff_pct"].apply(calculate_trade_percentage)

def generate_signal(trade_pct):
    if trade_pct > 0:
        return f"BUY {trade_pct * 100:.0f}%"
    elif trade_pct < 0:
        return f"SELL {-trade_pct * 100:.0f}%"
    else:
        return "HOLD"

df["trade_signal"] = df["trade_percentage"].apply(generate_signal)


print("Committing MySQL changes...")
conn.commit()
cursor.close()
conn.close()
print("MySQL Transaction Completed.")


print("Writing predictions to database...")
conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS given_period_stock_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock VARCHAR(20) NOT NULL,
        datetime DATETIME NOT NULL,
        close DECIMAL(10,2) NOT NULL,
        predicted_diff_pct DECIMAL(10,6),
        trade_percentage DECIMAL(10,6),
        trade_signal VARCHAR(20)
    );
""")

insert_query = """
    INSERT INTO given_period_stock_data (stock, datetime, close, predicted_diff_pct, trade_percentage, trade_signal)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

values_list = [
    (row["stock"], row["datetime"], row["close"], row["predicted_diff_pct"], row["trade_percentage"], row["trade_signal"])
    for _, row in df.iterrows() if not pd.isna(row["predicted_diff_pct"])
]

print(f"Inserting {len(values_list)} rows into database...")
cursor.executemany(insert_query, values_list)
conn.commit()

cursor.close()
conn.close()
print("All processes completed successfully.")
