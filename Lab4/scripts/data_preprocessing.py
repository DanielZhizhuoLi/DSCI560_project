import pymysql
import pandas as pd


DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()

# **读取数据**
query = "SELECT stock, datetime, close, high, low, open, volume FROM stock_data;"
df = pd.read_sql_query(query, conn)


df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values(by=["stock", "datetime"]).reset_index(drop=True)

# **检查缺失值**
if df.isna().sum().sum() > 0:
    print("Handling missing values...")
    df.interpolate(method="linear", inplace=True)


df["daily_return"] = df.groupby("stock")["close"].pct_change()
df["SMA_10"] = df.groupby("stock")["close"].transform(lambda x: x.rolling(window=10, min_periods=1).mean())
df["EMA_10"] = df.groupby("stock")["close"].transform(lambda x: x.ewm(span=10, adjust=False).mean())
df["volatility"] = df.groupby("stock")["daily_return"].transform(lambda x: x.rolling(window=10, min_periods=1).std())


window_length = 14
delta = df.groupby("stock")["close"].diff()

gain = (delta.where(delta > 0, 0)).groupby(df["stock"]).transform(lambda x: x.rolling(window=window_length, min_periods=1).mean())
loss = (-delta.where(delta < 0, 0)).groupby(df["stock"]).transform(lambda x: x.rolling(window=window_length, min_periods=1).mean())

RS = gain / loss
df["RSI"] = 100 - (100 / (1 + RS))


df.dropna(inplace=True)


cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_stock_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock VARCHAR(20) NOT NULL,
        datetime DATETIME NOT NULL,
        close DECIMAL(10,2) NOT NULL,
        daily_return DECIMAL(15,8),
        SMA_10 DECIMAL(10,2),
        EMA_10 DECIMAL(10,2),
        volatility DECIMAL(15,8),
        RSI DECIMAL(10,2)
    );
""")

# **批量插入数据**
insert_query = """
    INSERT INTO processed_stock_data (stock, datetime, close, daily_return, SMA_10, EMA_10, volatility, RSI)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
values_list = [
    (row["stock"], row["datetime"].strftime('%Y-%m-%d %H:%M:%S'), row["close"], row["daily_return"],
     row["SMA_10"], row["EMA_10"], row["volatility"], row["RSI"])
    for _, row in df.iterrows()
]

cursor.executemany(insert_query, values_list)
conn.commit()

# **关闭数据库连接**
cursor.close()
conn.close()

print("Stock data processing complete!")
