# indexing.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class PDFVectorStore:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        """t
        embedding_model: any model compatible with SentenceTransformers
        """
        self.model = SentenceTransformer(embedding_model)
        self.index = None
        self.chunks = []

    def add_documents(self, text_chunks):
        """
        Embed chunks and add them to the FAISS index.
        """
        self.chunks.extend(text_chunks)
        embeddings = self.model.encode(text_chunks, convert_to_numpy=True)
        if self.index is None:
            d = embeddings.shape[1]  # dimension of embeddings
            self.index = faiss.IndexFlatL2(d)
        self.index.add(embeddings)

    def search(self, query, top_k=3):
        """
        Perform a similarity search and return the top_k chunks.
        """
        query_vec = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vec, top_k)
        results = []
        for idx in indices[0]:
            results.append(self.chunks[idx])
        return results