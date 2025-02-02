# Stock Price Analysis and Algorithmic Trading

# setup

Installation

```pip install pandas numpy yfinance pymysal```

Create Mysql Database in mysql

```CREATE DATABASE stock```

Make sure table exists

```
CREATE TABLE IF NOT EXISTS stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock VARCHAR(20) NOT NULL,
    datetime DATETIME NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    open DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL
);
```

## Data Collection / Storage
In data_collection.py, we collect a list of stock in our portfolio using yfinance API calls by inputing the stock ticker, period, and interval. 
After getting the raw data, we clean up missing values to make sure no error message raise when storing data into mysql localhost.
We later connect our mysql localhost using pymysql, and query the desire format and store it in stock table

## Data Preprocessing
In data_preprocessing.py, we deal with missing values using interpolation fill, we then transform data by converting timestamps and calculating 
key financial metrics including Daily Returns, SMA(10day), EMA(10day), Volatility, after that we put the processed data in to mysql.


## Portfolio Altering
In audit_portfolio.py, we have operations such as adding a stock to the portfolio, removing a stock from the portfolio, displaying all their portfolios