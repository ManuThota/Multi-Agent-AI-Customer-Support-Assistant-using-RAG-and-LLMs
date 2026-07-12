import os
import json
import numpy as np
import faiss
import sys
from sentence_transformers import SentenceTransformer

# Add the backend root directory to the python path to resolve app imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.config import settings

class RAGRetriever:
    def __init__(self):
        self.vector_dir = settings.VECTORSTORE_DIR
        self.index_path = os.path.join(self.vector_dir, "index.faiss")
        self.metadata_path = os.path.join(self.vector_dir, "metadata.json")
        
        self.model = None
        self.index = None
        self.metadata = None
        self.initialized = False
        
    def initialize(self):
        """Loads model and index files into memory."""
        if self.initialized:
            return True
            
        if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
            print("Vectorstore files not found. Ingestion is required first.")
            return False
            
        try:
            print("Loading Sentence Transformer model ('all-MiniLM-L6-v2')...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            print("Loading FAISS Index...")
            self.index = faiss.read_index(self.index_path)
            
            print("Loading metadata mappings...")
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
                
            self.initialized = True
            print("RAG Retriever initialized successfully.")
            return True
        except Exception as e:
            print(f"Failed to initialize RAG Retriever: {str(e)}")
            return False
            
    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieves top_k context chunks matches for the query."""
        if not self.initialize():
            return []
            
        # Embed the search query
        query_vector = self.model.encode([query]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            chunk_data = self.metadata[idx]
            results.append({
                "text": chunk_data["text"],
                "source": chunk_data["metadata"]["source"],
                "heading": chunk_data["metadata"]["heading"],
                "distance": float(distances[0][rank])
            })
            
        return results

# Singleton instance for imports
retriever = RAGRetriever()

if __name__ == "__main__":
    # Test script for manual verification
    ret = RAGRetriever()
    if ret.initialize():
        test_queries = [
            "How do I reset my Smart Hub?",
            "What is the return window for a refund?",
            "How much is premium membership?"
        ]
        
        for q in test_queries:
            print("\n" + "="*50)
            print(f"QUERY: {q}")
            print("="*50)
            matches = ret.retrieve(q, top_k=2)
            for i, match in enumerate(matches):
                print(f"\nMatch {i+1} (Source: {match['source']} -> {match['heading']}):")
                print(f"Content: {match['text']}")
    else:
        print("Please run 'python backend/app/rag/ingestor.py' first to build the index.")