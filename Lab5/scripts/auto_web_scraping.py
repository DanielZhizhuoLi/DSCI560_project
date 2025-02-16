import praw
from dotenv import load_dotenv
import os
import pymysql
import time
import schedule

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "reddit"


load_dotenv()

client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
user_agent = os.getenv('REDDIT_USER_AGENT')




reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent
)

def connect_db():
	return pymysql.connect(host = DB_HOST, user= DB_USER, password=DB_PASSWORD, database=DB_NAME)

def check_duplicates(cursor, post_id):
    cursor.execute("SELECT id FROM posts WHERE id = %s", (post_id, ))
    return cursor.fetchone() is not None

def scrape_data():
	print("[INFO] Start scrape reddit data ...")
	# limit of 100 posts per request
	limit = 100
	total_posts = 0
	target_posts = 5000
	message = {}
	after = None
	request_count = 0
	while total_posts < target_posts:
		if after:
			hot_posts = reddit.subreddit("tech").hot(limit = limit, params = {"after": after})
		else:
			hot_posts = reddit.subreddit("tech").hot(limit = limit)
		last_post = None
		for post in hot_posts:
			title = post.title
			id = post.id
			message[id] = title
			total_posts += 1
			last_post = post
			print(f"post: {total_posts}")
		after = last_post.fullname if last_post else None
		request_count += 1
		print(f"requests: {request_count}")
		# limit of 100 queries per minute 
		if request_count >= 100:
			print("wait for 1 minute to scrape")
			time.sleep(60)
			request_count = 0
	return message

def insert_data(data):
	print("[INFO] Start insert data into posts...")
	conn = connect_db()
	cursor = conn.cursor()
	cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id VARCHAR(20) PRIMARY KEY,
        content TEXT
    );
    ''')
	for index, row in data.items():
	    if not check_duplicates(cursor, index):
		    sql = """INSERT INTO posts (id, content)
			    VALUE(%s, %s)"""
		    values = (index, row)
		    cursor.execute(sql, values)
	conn.commit()
	cursor.close()
	conn.close()
	print(f"Data saved successfully")

def scheduled_task():
	print("\n[INFO] Running scheduled Reddit scraping job ...")
	raw_data = scrape_data()
	insert_data(raw_data)
	print("\n[INFO] Job completed successfully. \n")




if __name__ == "__main__":
	interval_minutes = int(input("interval minutes: "))
	schedule.every(interval_minutes).minutes.do(scheduled_task)
	print(f"[INFO] Starting Reddit scraper. Running every {interval_minutes} minutes ...")
	while True:
		schedule.run_pending()
		time.sleep(1)
