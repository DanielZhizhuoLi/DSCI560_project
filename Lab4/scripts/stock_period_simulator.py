import pymysql
import pandas as pd

# Database connection parameters
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

# Connect to MySQL
conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cursor = conn.cursor()
print("Connected to MySQL.")

# Query to fetch stock and trading data
query = """
    SELECT p.datetime, p.stock, p.close AS price, t.trade_signal, t.trade_percentage
    FROM processed_stock_data p
    JOIN given_period_stock_data t 
      ON p.stock = t.stock AND p.datetime = t.datetime
    WHERE p.stock = 'AAPL'
      AND p.datetime BETWEEN '2023-01-01 00:00:00' AND '2025-01-01 23:59:59'
    ORDER BY p.datetime ASC;
"""
df = pd.read_sql_query(query, conn)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values(by="datetime").reset_index(drop=True)

# Close the MySQL connection (data has been loaded into df)
cursor.close()
conn.close()
print("Fetched data from MySQL.")

# Initialize Portfolio with a $100,000 initial investment
initial_investment = 50000.0
initial_price = df.iloc[0]["price"]

# Calculate how many whole shares can be purchased on the first day
initial_stocks = int(initial_investment // initial_price)
# Remaining cash after buying shares
cash_balance = initial_investment - (initial_stocks * initial_price)
initial_portfolio_value = initial_investment  # This is simply our starting money

print(f"Initial Price: ${initial_price:.2f}")
print(f"Initial Stocks Purchased: {initial_stocks}")
print(f"Initial Cash Balance: ${cash_balance:.2f}")

# Add portfolio columns to DataFrame
df["stocks_held"] = initial_stocks
df["cash_balance"] = cash_balance

# Simulate trading over the period
for i in range(len(df)):
    trade = df.loc[i, "trade_signal"]
    price = df.loc[i, "price"]
    trade_percentage = df.loc[i, "trade_percentage"]
    # For the first row, we already set initial values
    current_stocks = df.loc[i - 1, "stocks_held"] if i > 0 else initial_stocks
    current_cash = df.loc[i - 1, "cash_balance"] if i > 0 else cash_balance

    if "BUY" in trade:
        # Calculate how many shares to buy based on current holdings and trade percentage
        buy_stocks = int(current_stocks * trade_percentage)
        cost = buy_stocks * price
        if current_cash >= cost:
            df.loc[i, "stocks_held"] = current_stocks + buy_stocks
            df.loc[i, "cash_balance"] = current_cash - cost
        else:
            # Not enough cash to execute the trade; do nothing
            df.loc[i, "stocks_held"] = current_stocks
            df.loc[i, "cash_balance"] = current_cash

    elif "SELL" in trade:
        # Calculate how many shares to sell based on current holdings and trade percentage
        sell_stocks = int(current_stocks * abs(trade_percentage))
        revenue = sell_stocks * price
        df.loc[i, "stocks_held"] = current_stocks - sell_stocks
        df.loc[i, "cash_balance"] = current_cash + revenue

    else:
        # No trade signal; maintain the previous values
        df.loc[i, "stocks_held"] = current_stocks
        df.loc[i, "cash_balance"] = current_cash

# Calculate final portfolio value
final_stocks = df.loc[len(df) - 1, "stocks_held"]
final_price = df.loc[len(df) - 1, "price"]
final_cash = df.loc[len(df) - 1, "cash_balance"]
final_portfolio_value = final_stocks * final_price + final_cash

# Print Portfolio Summary
print("\nTrading Simulation Results")
print(f"Start Date: {df.iloc[0]['datetime']}")
print(f"End Date: {df.iloc[-1]['datetime']}")
print("")
print(f"Initial Investment: ${initial_investment:.2f}")
print(f"Initial Stocks: {initial_stocks}")
print(f"Initial Price: ${initial_price:.2f}")
print(f"Initial Cash Balance: ${cash_balance:.2f}")
print(f"Initial Portfolio Value: ${initial_portfolio_value:.2f}")
print("")
print(f"Final Stocks: {final_stocks}")
print(f"Final Price: ${final_price:.2f}")
print(f"Final Cash: ${final_cash:.2f}")
print(f"Final Portfolio Value: ${final_portfolio_value:.2f}")
