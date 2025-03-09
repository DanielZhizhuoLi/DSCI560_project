import os
import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

# Load dataset
df = pd.read_csv("posts.csv")  

# Prepare data for Doc2Vec
tagged_data = [TaggedDocument(words=row.split(), tags=[df['id'][idx]]) for idx, row in enumerate(df['content'])]

# Define different Doc2Vec configurations
configurations = [
    {"vector_size": 50, "min_count": 2, "epochs": 20},
    {"vector_size": 100, "min_count": 1, "epochs": 30},
    {"vector_size": 200, "min_count": 2, "epochs": 40},
]

models = {}
embeddings_dict = {}

for i, config in enumerate(configurations):
    model = Doc2Vec(tagged_data, **config)
    models[f"Config_{i+1}"] = model
    model.save(f"{output_dir}/doc2vec_{i+1}.bin")
    embeddings = np.array([model.dv[tag] for tag in df['id']])
    embeddings_dict[f"Config_{i+1}"] = embeddings

# Store graph paths
graph_paths = []
best_bins = {}

# Reduce dataset for efficiency
if len(df) > 200:
    df_sampled = df.sample(n=200, random_state=42).reset_index(drop=True)
    sampled_embeddings_dict = {k: np.array([models[k].dv[tag] for tag in df_sampled['id']]) for k in models}
else:
    df_sampled = df
    sampled_embeddings_dict = embeddings_dict

# Loop through different Doc2Vec configurations
for config_name, embeddings in sampled_embeddings_dict.items():

    pca_dim = 25
    pca = PCA(n_components=pca_dim)
    reduced_embeddings = pca.fit_transform(embeddings)

    # Compute WCSS using MiniBatchKMeans
    wcss = []
    silhouette_scores = {}
    optimized_K_range = range(3, 15)  

    for k in optimized_K_range:
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=512, max_iter=100)
        labels = kmeans.fit_predict(reduced_embeddings)
        wcss.append(kmeans.inertia_)

        # Compute Silhouette Score
        silhouette_avg = silhouette_score(reduced_embeddings, labels)
        silhouette_scores[k] = silhouette_avg

    # Find the best bin count based on the highest Silhouette Score
    best_bin = max(silhouette_scores, key=silhouette_scores.get)
    best_bins[config_name] = best_bin
    print(f"Best bin for {config_name}: {best_bin} (Silhouette: {silhouette_scores[best_bin]:.4f})")

    # Save Elbow Plot
    plt.figure(figsize=(8, 5))
    plt.plot(optimized_K_range, wcss, marker='o', linestyle='--', color='b')
    plt.xlabel('Number of Clusters (K)')
    plt.ylabel('WCSS')
    plt.title(f'Elbow Method - {config_name}')
    elbow_plot_path = f"{output_dir}/elbow_{config_name}.png"
    plt.savefig(elbow_plot_path)
    plt.close()
    graph_paths.append(elbow_plot_path)

    # Perform clustering with the best bin
    kmeans = MiniBatchKMeans(n_clusters=best_bin, random_state=42, batch_size=512, max_iter=100)
    labels = kmeans.fit_predict(reduced_embeddings)

    # Reduce dimensions to 2D for visualization
    pca_2d = PCA(n_components=2)
    final_embeddings = pca_2d.fit_transform(reduced_embeddings)

    # Save Clustering Visualization
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=final_embeddings[:, 0], y=final_embeddings[:, 1], hue=labels, palette='viridis', alpha=0.7)
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], c='red', marker='X', s=200, label="Centroids")
    plt.title(f'KMeans Clustering - {config_name} (Best Bins: {best_bin})')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.legend()
    cluster_plot_path = f"{output_dir}/cluster_{config_name}.png"
    plt.savefig(cluster_plot_path)
    plt.close()
    graph_paths.append(cluster_plot_path)

# Print results
print("\nBest bin counts for each configuration based on Silhouette Score:")
for config, bin_count in best_bins.items():
    print(f" - {config}: {bin_count} clusters")

print("\nGraphs saved:", graph_paths)

