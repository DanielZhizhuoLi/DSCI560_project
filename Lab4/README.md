# Stock Price Analysis and Algorithmic Trading

## Setup

Installation

```pip install pandas numpy yfinance pymysal statsmodels matplotlib sqlalchemy pandas_ta plot_acf sklearn tensorflow```

Create Mysql Database in mysql

```CREATE DATABASE processed_stock_data```

Make sure table exists

```
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
```

## Data Collection / Storage
In data_collection.py, we collect a list of stocks in our portfolio (AAPL, TSLA, NVDA, LCID) using yfinance API calls by inputing the stock ticker, period, and interval. 
We collected the data from 2024-09-01 to 2024-11-30, interval = 1h.
After getting the raw data, we clean up missing values to make sure no error message is raised when storing data into mysql localhost.
We later connect our mysql localhost using pymysql, query the desired format and store it in the stock table

## Data Preprocessing
In data_preprocessing.py, we deal with missing values using interpolation fill, we then transform data by converting timestamps and calculating 
key financial metrics including Daily Returns, SMA(10day), EMA(10day), Volatility, RSI after that we put the processed data in to mysql.
