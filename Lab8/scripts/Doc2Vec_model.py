import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import pandas as pd


file_path = "posts.csv"  
df = pd.read_csv(file_path)

# Convert data into TaggedDocuments for Doc2Vec
tagged_data = [TaggedDocument(words=row['content'].split(), tags=[row['id']]) for _, row in df.iterrows()]

# Train Doc2Vec Model with a specific vector size
vector_size = 10  # comparing to Word2Vec
model = Doc2Vec(tagged_data, vector_size=vector_size, min_count=2, epochs=30)

model.save("doc2vec_model.bin")
print("Model saved successfully!")

# # Extract embeddings
# embeddings = [model.dv[tag] for tag in df['id']]


