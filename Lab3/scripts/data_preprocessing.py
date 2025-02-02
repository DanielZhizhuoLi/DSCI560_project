import pymysql
import pandas as pd

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

# Connect to MySQL
conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()

# Fetch stock data from MySQL
query = "SELECT stock, datetime, close, high, low, open, volume FROM stock_data;"
df = pd.read_sql(query, conn)



print(df.head())

# Convert datetime column to proper format
df['datetime'] = pd.to_datetime(df['datetime'])
df.set_index('datetime', inplace=True)

# Check for missing values before handling them
if df.isna().sum().sum() == 0:
    print("No NaN values found in the dataset.")
else:
    print("Missing values detected....")

    # Handling missing values
    df.interpolate(method='linear', inplace=True)  # Linear interpolation

    # Check again if NaN values still exist
    if df.isna().sum().sum() == 0:
        print("Missing values successfully handled.")
    else:
        print("Missing values still exist. Please check the dataset.")

# Calculate financial indicators
df['daily_return'] = df['close'].pct_change()
df['SMA_10'] = df['close'].rolling(window=10).mean()  # 10-day Simple Moving Average
df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()  # 10-day Exponential Moving Average
df['volatility'] = df['daily_return'].rolling(window=10).std()  # Rolling Volatility

# Drop NaN values created due to calculations
df.dropna(inplace=True)

# Save processed data back to MySQL
cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_stock_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock VARCHAR(20) NOT NULL,
        datetime DATETIME NOT NULL,
        close DECIMAL(10,2) NOT NULL,
        daily_return DECIMAL(10,6),
        SMA_10 DECIMAL(10,2),
        EMA_10 DECIMAL(10,2),
        volatility DECIMAL(10,6)
    );
""")

# Insert transformed data back to MySQL
for index, row in df.iterrows():
    sql = """
        INSERT INTO processed_stock_data (stock, datetime, close, daily_return, SMA_10, EMA_10, volatility)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (row.name, index.strftime('%Y-%m-%d %H:%M:%S'), row["close"], row["daily_return"], row["SMA_10"], row["EMA_10"], row["volatility"])
    cursor.execute(sql, values)

# Commit and close connection
conn.commit()
cursor.close()
conn.close()

print("Stock data processing complete!")
