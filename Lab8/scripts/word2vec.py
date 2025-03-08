import nltk
import gensim
from gensim.models import Word2Vec
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import euclidean_distances
import matplotlib.pyplot as plt
import numpy as np

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


def vectorization(tokens, dim):
	model = gensim.models.Word2Vec(tokens, min_count= 1, vector_size = dim, window = 5)
	words = list(model.wv.index_to_key)
	word_vectors = {word: model.wv[word] for word in words}
	return words, word_vectors

dim_25_words, dim_25_vectors = vectorization(tokens, 25)
dim_50_words, dim_50_vectors = vectorization(tokens, 50)
dim_100_words, dim_100_vectors = vectorization(tokens, 100)

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
	plt.figure(figsize=(8,5))
	plt.plot(range(1, 16), wcss, marker= 'o', linestyle='--')
	plt.xlabel("Number of Clusters (K)")
	plt.ylabel("WCSS")
	plt.title("dim 100 elbow method")
	plt.savefig(f"../data/word2vec/dim_100_elbow_plot.png")
	plt.close()
	return 
# plot_elbow(dim_25_vectors)
# plot_elbow(dim_50_vectors)
plot_elbow(dim_100_vectors)

def get_bins(vectors, n_clusters):
	words = list(vectors.keys())
	vector_values  = np.array(list(vectors.values()))
	kmeans = KMeans(n_clusters = n_clusters, random_state = 42)
	kmeans.fit(vector_values)
	labels = kmeans.labels_
	bins = {i: [] for i in range(n_clusters)}
	for word, label in zip(words, labels):
		bins[label].append(word)
	return bins

# dim 25 get 4 bins
dim_25_bins = get_bins(dim_25_vectors, 4)
# dim 50 get 6 bins
dim_50_bins = get_bins(dim_50_vectors, 6)
# dim 100 get 7 bins
dim_100_bins = get_bins(dim_100_vectors, 7)

def bag_of_word(tokens, bins, n):
	bow = []
	for post in tokens:
		bin_count = [0] * n
		for word in post:
			for bin_id, bin_words in bins.items():
				if word in bin_words:
					bin_count[bin_id] += 1
					break
		bow.append(bin_count)
	return bow

dim_25_bow = bag_of_word(tokens, dim_25_bins, 4)
dim_50_bow = bag_of_word(tokens, dim_50_bins, 6)
dim_100_bow = bag_of_word(tokens, dim_100_bins, 7)

def normalization(bow):
	norms_bow = []
	for bow_count in bow:
		max_count = max(bow_count)
		if max_count > 0:
			norms_bow.append([count / max_count for count in bow_count])
		else:
			norms_bow.append([0]* len(bow_count))
	return norms_bow

dim_25_norms_bow = normalization(dim_25_bow)
dim_50_norms_bow = normalization(dim_50_bow)
dim_100_norms_bow = normalization(dim_100_bow)


# merge_df = pd.concat([df_bow_25, df_bow_50, df_bow_100], axis = 1)
# merge_df.to_csv("../data/word2vec_vectors.csv", index=False)
# print("sucessfully ouput as csv")


def clustering(norms_bow, n_clusters):
	kmeans = KMeans(n_clusters= n_clusters, random_state = 42)
	kmeans.fit(norms_bow)
	centroids = kmeans.cluster_centers_

	distances = euclidean_distances(centroids, norms_bow)
	closest_posts = np.argmin(distances, axis = 1)
	return kmeans, centroids, closest_posts

pca = PCA(n_components= 2)

# dimension of 25 
dim_25_kmeans_model, dim_25_centroids, dim_25_closest_posts = clustering(dim_25_norms_bow, 4)
dim_25_reduced_pca = pca.fit_transform(dim_25_norms_bow)
dim_25_reduced_centroids = pca.fit_transform(dim_25_centroids)

plt.figure(figsize = (10,6))
plt.scatter(dim_25_reduced_pca[:, 0], dim_25_reduced_pca[:, 1], c=dim_25_kmeans_model.labels_, cmap='viridis', marker='.')
plt.scatter(dim_25_reduced_centroids[:, 0], dim_25_reduced_centroids[:, 1], c='red', marker='x', s= 100, label= 'Centroids')
for i, closest_post in enumerate(dim_25_closest_posts):
	plt.annotate(f'Post {closest_post +1}', (dim_25_reduced_pca[closest_post, 0], dim_25_reduced_pca[closest_post, 1]), textcoords="offset points", xytext=(0, 5), ha='center')

plt.xlabel("pca 1")
plt.ylabel("pca 2")
plt.title("Kmeans cluster with centroids and closest posts")
plt.legend()
plt.savefig("../data/word2vec/dim_25_clustering.png")
plt.close()
print("dim 25 cluster is saved")


# dimension of 50 
dim_50_kmeans_model, dim_50_centroids, dim_50_closest_posts = clustering(dim_50_norms_bow, 6)
dim_50_reduced_pca = pca.fit_transform(dim_50_norms_bow)
dim_50_reduced_centroids = pca.fit_transform(dim_50_centroids)

plt.figure(figsize = (10,6))
plt.scatter(dim_50_reduced_pca[:, 0], dim_50_reduced_pca[:, 1], c=dim_50_kmeans_model.labels_, cmap='viridis', marker='.')
plt.scatter(dim_50_reduced_centroids[:, 0], dim_50_reduced_centroids[:, 1], c='red', marker='x', s= 100, label= 'Centroids')
for i, closest_post in enumerate(dim_50_closest_posts):
	plt.annotate(f'Post {closest_post +1}', (dim_50_reduced_pca[closest_post, 0], dim_50_reduced_pca[closest_post, 1]), textcoords="offset points", xytext=(0, 5), ha='center')

plt.xlabel("pca 1")
plt.ylabel("pca 2")
plt.title("Kmeans cluster with centroids and closest posts")
plt.legend()
plt.savefig("../data/word2vec/dim_50_clustering.png")
plt.close()
print("dim 50 cluster is saved")



# dimension of 100
dim_100_kmeans_model, dim_100_centroids, dim_100_closest_posts = clustering(dim_100_norms_bow, 7)
dim_100_reduced_pca = pca.fit_transform(dim_100_norms_bow)
dim_100_reduced_centroids = pca.fit_transform(dim_100_centroids)

plt.figure(figsize = (10,6))
plt.scatter(dim_100_reduced_pca[:, 0], dim_100_reduced_pca[:, 1], c=dim_100_kmeans_model.labels_, cmap='viridis', marker='.')
plt.scatter(dim_100_reduced_centroids[:, 0], dim_100_reduced_centroids[:, 1], c='red', marker='x', s= 100, label= 'Centroids')
for i, closest_post in enumerate(dim_100_closest_posts):
	plt.annotate(f'Post {closest_post +1}', (dim_100_reduced_pca[closest_post, 0], dim_100_reduced_pca[closest_post, 1]), textcoords="offset points", xytext=(0, 5), ha='center')

plt.xlabel("pca 1")
plt.ylabel("pca 2")
plt.title("Kmeans cluster with centroids and closest posts")
plt.legend()
plt.savefig("../data/word2vec/dim_100_clustering.png")
plt.close()
print("dim 100 cluster is saved")



def calculate_silhouette_score(vec, labels):
	score = silhouette_score(vec, labels)
	return score

silhouette_25 = calculate_silhouette_score(dim_25_norms_bow, dim_25_kmeans_model.labels_)
silhouette_50 = calculate_silhouette_score(dim_50_norms_bow, dim_50_kmeans_model.labels_)
silhouette_100 = calculate_silhouette_score(dim_100_norms_bow, dim_100_kmeans_model.labels_)


print(f"Silhouette score for word2vec 25-dimension vectors: {silhouette_25}")
print(f"Silhouette score for word2vec 50-dimension vectors: {silhouette_50}")
print(f"Silhouette score for word2vec 100-dimension vectors: {silhouette_100}")