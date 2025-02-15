from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
from sqlalchemy import create_engine, text


DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "reddit"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")


def get_data(engine):
	query = 'SELECT * FROM processed_data;'
	df = pd.read_sql(query, engine)
	return df

df = get_data(engine)
vectors = []
for vector in df['vector']:
	vectors.append(np.array(json.loads(vector)))

x = np.array(vectors)
def find_k(x):
	wcss = []
	for k in range(1, 11):
		kmeans = KMeans(n_clusters = k, random_state = 42)
		kmeans.fit(x)
		wcss.append(kmeans.inertia_)

	plt.plot(range(1,11), wcss)
	plt.title('Elbow Method for optimal k')
	plt.xlabel('Number of CLusters')
	plt.ylabel('WCSS (Inertia)')
	plt.savefig("../data/elbow_method_kmeans.png")
	plt.close()
	print("fig is saved")

#find_k(x)

# standardize vectors
scaler = StandardScaler()
x_scaled = scaler.fit_transform(x)


doc_vectors = np.array([np.array(json.lodas(vec) for vec in df['vector'])])
kmeans = KMeans(n_clusters = 2, random_state = 42)
kmeans.fit(x_scaled)

centroids = kmeans.cluster_centers_

pca =  PCA(n_components = 2)
x_pca = pca.fit_transform(x_scaled)

plt.figure(figsize=(8,6))
plt.scatter(x_pca[:, 0], x_pca[:,1], c=kmeans.labels_, cmap = 'viridis', s = 50, alpha = 0.6, edgecolors = 'k')

#plot centroids
centroids_pca = pca.transform(centroids)
plt.scatter(centroids_pca[:,0], centroids_pca[:,1], c='red', s=200, marker= 'x', label='Centroids')

# identify the points around centroids
closes_docs = []
for i, centroid in enumerate(centroids):
	distance = np.linalg.norm(doc_vectors - centroid, axis = 1)
	closest_idx = np.aragmin(distance)
	closest_docs.append({
		'cluster': i,
		'id': df.iloc[closest_idx]['id'],
	'content': df.iloc[closest_idx]['content']})

for doc in close_docs:
	print(f"cluster {doc['cluster']}:")
	print(f"closest document ID: {doc['id']}")
	print(f"content {doc['content']}")
	print()

plt.scatter(doc_vectors[:,0], doc_vectors[:, 1], c=labels, cmap='viridis')
plt.scatter(centroids[:0], cnetroids[:,1], s =300, c='red', marker='x')
plt.title("KMeans Clusters and Centroids")
plt.savefig("../data/kmeans_and_centroids.png")
plt.close()
