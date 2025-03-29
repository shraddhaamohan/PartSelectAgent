import os
os.environ["TOKENIZERS_PARALLELISM"] = "false" 
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
import pickle

class FaissIndexer:
    def __init__(self, data_list, model_name="all-MiniLM-L6-v2"):
        """
        data_list is the list of troubleshoot info dicts, e.g. dishwasherTroubleshoot or refrigeratorTroubleshoot
        model_name is the name of the SentenceTransformer model to use for embeddings.
        """
        self.data_list = data_list
        self.index = None
        self.embeddings = []
        self.metadata = []
        self.model = SentenceTransformer(model_name)
        
    def create_index(self):
        # Process the entire data list without batching
        for item in self.data_list:
            # Generate embedding for the title and description
            title_text = f"{item['title']} - {item['description']}"
            title_embedding = self._get_embedding(title_text)
            self.embeddings.append(title_embedding)
            self.metadata.append({"type": "title", "data": item})

            # Generate embeddings for each solution
            for solution in item.get("solutions", []):
                solution_text = f"{item['title']} - {solution['part']} - {solution['description']}"
                solution_embedding = self._get_embedding(solution_text)
                self.embeddings.append(solution_embedding)
                self.metadata.append({"type": "solution", "parent": item, "data": solution})

        # Normalize embeddings to unit vectors
        self.embeddings = normalize(np.array(self.embeddings).astype("float32"), axis=1)

        # Create the FAISS index for cosine similarity (Inner Product)
        dimensions = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimensions)
        self.index.add(self.embeddings)

    def search(self, query, k=3):
        # Generate embedding for the query and normalize it
        query_embedding = self._get_embedding(query)
        query_embedding = normalize(np.array([query_embedding]).astype("float32"), axis=1)

        # Perform the search
        distances, indices = self.index.search(query_embedding, k)

        # Convert distances to similarity scores (cosine similarity)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            results.append({"score": float(dist), "data": self.metadata[idx]})
        return results

    def _get_embedding(self, text):
        # Generate embedding using SentenceTransformers
        return self.model.encode(text)
    
    def save_index(self, index_path="faiss_index.bin", metadata_path="metadata.pkl"):
        """
        Save the FAISS index and metadata to disk.
        """
        # Save the FAISS index
        faiss.write_index(self.index, index_path)
        print(f"FAISS index saved to {index_path}")

        # Save the metadata
        with open(metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"Metadata saved to {metadata_path}")

    def load_index(self, index_path="faiss_index.bin", metadata_path="metadata.pkl"):
        """
        Load the FAISS index and metadata from disk.
        """
        # Load the FAISS index
        self.index = faiss.read_index(index_path)
        print(f"FAISS index loaded from {index_path}")

        # Load the metadata
        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)
        print(f"Metadata loaded from {metadata_path}")