import pymysql
import yfinance as yf
from datetime import datetime
from data_collection import insert_data, download_stock

# Database connection parameters
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2001620lzzA"
DB_NAME = "stock"


def connect_db():
    """Establish connection to MySQL."""
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)


def get_stocks():
    """Retrieve distinct stock names and their first added time."""
    conn = connect_db()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT stock, MAX(datetime) AS first_added 
        FROM stock_data 
        GROUP BY stock
        ORDER BY first_added ASC;
    """
    cursor.execute(query)
    stocks = cursor.fetchall()

    if not stocks:
        print("No stocks available in the database.")
    else:
        print("Current Stocks in Database:")
        for stock, added_time in stocks:
            print(f"{stock} - First Added: {added_time.strftime('%Y-%m-%d %H:%M:%S')}")

    cursor.close()
    conn.close()
    return stocks


def add_stock():
    """Add a new stock to the database using the existing function."""
    stock = input("Enter stock ticker (e.g., AAPL): ").strip().upper()

    # Validate stock using yfinance
    stock_data = yf.Ticker(stock)
    info = stock_data.info
    if 'shortName' not in info:
        print(f"Invalid stock name '{stock}'. Please enter a valid ticker symbol.")
        return

    print(f"Valid stock '{stock}' detected. Fetching data...")

    # download and insert stock data
    data = download_stock(stock)
    insert_data(stock, data)

    print(f" Stock '{stock}' added successfully!")


def delete_stock():
    """Delete all records of a stock from the database."""
    stock = input("Enter stock ticker to delete (e.g., AAPL): ").strip().upper()

    conn = connect_db()
    cursor = conn.cursor()

    # Check if stock exists
    cursor.execute("SELECT COUNT(*) FROM stock_data WHERE stock = %s", (stock,))
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"Stock '{stock}' not found in database.")
    else:
        cursor.execute("DELETE FROM stock_data WHERE stock = %s", (stock,))
        conn.commit()
        print(f"Stock '{stock}' removed successfully.")

    cursor.close()
    conn.close()


def main():
    while True:

        print("1 View available stocks")
        print("2 Add a new stock")
        print("3⃣ Delete a stock")
        print("4 Exit")

        choice = input("Choose an option (1-4): ")

        if choice == '1':
            get_stocks()
        elif choice == '2':
            add_stock()
        elif choice == '3':
            delete_stock()
        elif choice == '4':
            break
        else:
            print("Invalid choice! Please choose between 1-4.")


if __name__ == "__main__":
    main()
