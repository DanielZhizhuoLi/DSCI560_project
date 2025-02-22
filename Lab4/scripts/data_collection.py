import yfinance as yf
import pandas as pd
import numpy
import pymysql

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"

def download_stock(ticker, start="2023-01-01", end="2025-01-01", interval="1d"):
    stock_data = yf.download(tickers=ticker, start=start, end=end, interval=interval)
    return stock_data
def connect_db():
	return pymysql.connect(host = DB_HOST, user= DB_USER, password=DB_PASSWORD, database=DB_NAME)

def insert_data(ticker, data):
	conn = connect_db()
	cursor = conn.cursor()
	
	for index, row in data.iterrows():
		sql = """INSERT INTO stock_data (stock, datetime, close, high, low, open, volume)
			VALUE(%s, %s, %s, %s, %s, %s, %s)"""
		values = (str(ticker), index.strftime('%Y-%m-%d %H:%M:%S'), float(row["Close"]), float(row["High"]), float(row["Low"]), float(row["Open"]), float(row["Volume"]))
		cursor.execute(sql, values)
	conn.commit()
	cursor.close()
	conn.close()
	print(f"Data for {ticker} saved successfully")

# ticker = input("stock: ")
# stock_data = download_stock(ticker, input("period: "), input("interval: "))
# insert_data(ticker, stock_data)


if __name__ == '__main__':

	with open('initial_portfolio.txt', 'r') as file:
		stocks = file.read().split(',')

		for stock in stocks:
			stock_data = download_stock(stock)
			insert_data(stock, stock_data)


