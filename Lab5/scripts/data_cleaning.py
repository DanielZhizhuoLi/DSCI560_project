import nltk
import gensim
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
from sqlalchemy import create_engine, text
import json

# download stopwords 
nltk.download('stopwords')
nltk.download('punkt')

stop_words = set(stopwords.words('english'))

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "reddit"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")


def get_data(engine):
	query = 'SELECT * FROM posts;'
	df = pd.read_sql(query, engine)
	return df

def insert_data(engine, ids, contents, vectors):
	with engine.connect() as conn:
		conn.execute(text(
		'''
		CREATE TABLE IF NOT EXISTS processed_data (
        	id VARCHAR(20) PRIMARY KEY,
        	content TEXT,
        	vector JSON
		);
		'''))
		conn.commit()
		if not vectors:
			print("No vectors to insert")
			return

		for index, (content, vector) in enumerate(zip(contents, vectors)):
			original_id = str(ids[index])
			if vector is not None:
				vector_json = json.dumps(vector.tolist())
			else:
				vector_json = None
			query = text("""INSERT INTO processed_data (id, content, vector)
			VALUES (:id, :content, :vector)""")
			values = {
				"id": original_id, 
				"content": content,
				"vector": vector_json
			}
			conn.execute(query, values)

		conn.commit()
	print(f"Data is saved successfully")

def read_corpus(document):
	for i, line in enumerate(document):
		tokens = gensim.utils.simple_preprocess(line)
		yield gensim.models.doc2vec.TaggedDocument(tokens, [i])

# get the data from posts 
df = get_data(engine)
documents = df['content']
ids = df['id']

# embedding the posts
corpus = list(read_corpus(documents))

# Embedding the corpus
model = gensim.models.doc2vec.Doc2Vec(vector_size=50, min_count=2, epochs=40)
model.build_vocab(corpus)
model.train(corpus, total_examples=model.corpus_count, epochs=model.epochs)

doc_vectors = [model.dv[i] for i in range(len(corpus))]

print(f"Total documents: {len(doc_vectors)}, Embedding size: {len(doc_vectors[0])}")

# store vectors into database
insert_data(engine, ids, documents, doc_vectors)


