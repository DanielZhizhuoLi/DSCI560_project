import nltk
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd

# download stopwords 
nltk.download('stopwords')
nltk.donwload('punkt')

stop_words = set(stopwords.words('english'))

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "reddit"

def connect_db():
	return pymysql.connect(host = DB_HOST, user= DB_USER, password=DB_PASSWORD, database=DB_NAME)

def get_data():
	conn = connect_db()
	query = 'SELECT * FROM posts;'
    	df = pd.read_sql(query, conn)
	return df

for index, row in df.itesrrow():
	text = row["content"]
	
