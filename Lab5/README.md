# Reddit Post Scraper

## Setup

### Installation

```pip install pandas, numpy, python-dotenv, praw, pymql, matplotlib, nltk, gensim, json, scikit-learn, time, schedule```

### Create Mysql Database in mysql

```CREATE DATABASE reddit```

### Make sure table exists

Create posts table to store raw data

```
CREATE TABLE IF NOT EXISTS posts (
    id VARCHAR(20) PRIMARY KEY,
    content TEXT
);
```



Create processed_data to store vectors

```
CREATE TABLE IF NOT EXISTS processed_data (
    id VARCHAR(20) PRIMARY KEY,
    content TEXT,
    vector JSON
);
```

## Data Collection / Storage
In auto_web_scraping.py, we collect a number of hot posts in "/tech" subreddit and scrape as many as we can. 
We rest the script to not exceed the limit of requesting in Reddit API, 100 request over a minute.
After scraping, we store the raw data in the post table in reddit database.


## Data Preprocessing
In data_cleaning.py, we first removed the stopwords and punctuations. Later, we vectorized the text in each posts.
Lastly use the doc2vec model to embed the vector into a numeric representation, length of 50.
After all the data preprocessing, we can pass the data to KMeans cluster to classify the posts into groups.
