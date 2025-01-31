# Stock Price Analysis and Algorithmic Trading

## Data Collection / Storage
In data_collection.py, we collect a list of stock in our portfolio using yfinance API calls by inputing the stock ticker, period, and interval. 
After getting the raw data, we clean up missing values to make sure no error message raise when storing data into mysql localhost.
We later connect our mysql localhost using pymysql, and query the desire format and store it in stock table

## Data Preprocessing


