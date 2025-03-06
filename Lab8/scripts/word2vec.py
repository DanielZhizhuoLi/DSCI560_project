import nltk
import gensim
from gensim.models import Word2Vec
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
import pymysql
from sqlalchemy import create_engine
import json
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict 

# download stopwords 
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')



DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "reddit"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

def get_data(engine):
	query = 'SELECT * FROM posts;'
	df = pd.read_sql(query, engine)
	return df

# get the data from posts 
df = get_data(engine)


def tokenization(df):
	stop_words = set(stopwords.words('english'))
	tokenized_sentences = []
	for row in df['content']:
		tokens = word_tokenize(row.lower())
		# check the token is not a stopword and not contain number
		filter_tokens = [token for token in tokens if token not in stop_words and token.isalnum()]
		tokenized_sentences.append(filter_tokens)
	return tokenized_sentences

tokens = tokenization(df)
print(f"total tokens in all the data: {len(tokens)}")


def vectorization(tokens):
	model = gensim.models.Word2Vec(tokens, min_count= 1, vector_size = 50, window = 5)
	words = list(model.wv.index_to_key)
	word_vectors = {word: model.wv[word] for word in words}
	return words, word_vectors

words, vectors = vectorization(tokens)

def find_k(word_vectors):
	vector_values  = np.array(list(word_vectors.values()))
	wcss = []
	for k in range(1, 16):
		kmeans = KMeans(n_clusters = k, random_state = 42)
		kmeans.fit(vector_values )
		wcss.append(kmeans.inertia_)
	return wcss

def plot_elbow(vectors):
	wcss = find_k(vectors)
	# found k = 6 is optimal 
	plt.figure(figsize=(8,5))
	plt.plot(range(1, 16), wcss, marker= 'o', linestyle='--')
	plt.xlabel("Number of Clusters (K)")
	plt.ylabel("WCSS")
	plt.savefig("elbow_plot.png")
	plt.close()
	return 
#plot_elbow()

def get_bins(vectors):
	words = list(vectors.keys())
	vector_values  = np.array(list(vectors.values()))
	kmeans = KMeans(n_clusters = 6, random_state = 42)
	kmeans.fit(vector_values)
	labels = kmeans.labels_
	bins = {i: [] for i in range(6)}
	for word, label in zip(words, labels):
		bins[label].append(word)
	return bins

bins = get_bins(vectors)

def bag_of_word(tokens, bins):
	bow = []
	for post in tokens:
		bin_count = [0] * 6
		for word in post:
			for bin_id, bin_words in bins.items():
				if word in bin_words:
					bin_count[bin_id] += 1
					break
		bow.append(bin_count)
	return bow

bow = bag_of_word(tokens, bins)

def normalization(bow):
	norms_bow = []
	for bow_count in bow:
		max_count = max(bow_count)
		if max_count > 0:
			norms_bow.append([count / max_count for count in bow_count])
		else:
			norms_bow.append([0]* len(bow_count))
	return norms_bow

norms_bow = normalization(bow)

def clustering(norms_bow):
	kmeans = KMeans(n_clusters= 6, random_state = 42)
	kmeans.fit(norms_bow)
	centroids = kmeans.cluster_centers_

	distances = euclidean_distances(centroids, norms_bow)
	closest_posts = np.argmin(distances, axis = 1)
	return kmeans, centroids, closest_posts

kmeans_model, centroids, closest_posts = clustering(norms_bow)
print(centroids)
pca = PCA(n_components= 2)
reduced_pca = pca.fit_transform(norms_bow)
reduced_centroids = pca.fit_transform(centroids)

plt.figure(figsize = (10,6))
plt.scatter(reduced_pca[:, 0], reduced_pca[:, 1], c=kmeans_model.labels_, cmap='viridis', marker='.')
plt.scatter(reduced_centroids[:, 0], reduced_centroids[:, 1], c='red', marker='x', s= 100, label= 'Centroids')
for i, closest_post in enumerate(closest_posts):
	plt.annotate(f'Post {closest_post +1}', (reduced_pca[closest_post, 0], reduced_pca[closest_post, 1]), textcoords="offset points", xytext=(0, 5), ha='center')

plt.xlabel("pca 1")
plt.ylabel("pca 2")
plt.title("Kmeans cluster with centroids and closest posts")
plt.legend()
plt.savefig("clustering.png")
plt.close()