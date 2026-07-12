import os
import re
import json
import numpy as np
import faiss
import sys
import logging
import warnings

# Suppress HuggingFace hub warnings and logs
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
from sentence_transformers import SentenceTransformer

# Add the backend root directory to the python path to resolve app imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.config import settings

def clean_text(text: str) -> str:
    """Removes excessive whitespace and standardizes formatting."""
    return re.sub(r'\s+', ' ', text).strip()

def split_text_by_words(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[str]:
    """Helper function to split text into chunks based on character/word limits."""
    words = clean_text(text).split(' ')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1  # Add 1 for the space
        
        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            # Approximate overlap by keeping the last portion of words
            overlap_count = max(1, int(chunk_overlap / 5))
            current_chunk = current_chunk[-overlap_count:]
            current_size = sum(len(w) + 1 for w in current_chunk)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def split_markdown_into_chunks(text: str, source_name: str) -> list[dict]:
    """Splits markdown files by headings to preserve structural context."""
    # Split using headings (e.g. #, ##, ###) while retaining them
    sections = re.split(r'\n(?=#{1,4} )', text)
    chunks = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Extract the heading for context metadata
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', section, re.MULTILINE)
        heading = heading_match.group(2).strip() if heading_match else "General"
        
        # If the section is too large, split it with overlap
        if len(section) > 600:
            sub_chunks = split_text_by_words(section, chunk_size=500, chunk_overlap=100)
            for sub in sub_chunks:
                chunks.append({
                    "text": sub,
                    "metadata": {
                        "source": source_name,
                        "heading": heading
                    }
                })
        else:
            chunks.append({
                "text": section,
                "metadata": {
                    "source": source_name,
                    "heading": heading
                }
            })
            
    return chunks

def ingest_documents():
    """Reads documents, creates embeddings, builds FAISS index and stores them."""
    print("Initializing document ingestion pipeline...")
    
    knowledge_dir = settings.KNOWLEDGE_BASE_DIR
    vector_dir = settings.VECTORSTORE_DIR
    
    # Ensure directories exist
    os.makedirs(vector_dir, exist_ok=True)
    
    if not os.path.exists(knowledge_dir):
        print(f"Error: Knowledge base directory '{knowledge_dir}' does not exist.")
        return False
        
    documents = [f for f in os.listdir(knowledge_dir) if f.endswith('.md')]
    if not documents:
        print(f"No markdown documents found in '{knowledge_dir}'. Please populate it first.")
        return False
        
    all_chunks = []
    for doc_name in documents:
        file_path = os.path.join(knowledge_dir, doc_name)
        print(f"Processing: {doc_name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            chunks = split_markdown_into_chunks(content, doc_name)
            all_chunks.extend(chunks)
            
    print(f"Total chunks created: {len(all_chunks)}")
    
    if not all_chunks:
        print("No content to embed.")
        return False
        
    # Extract only the texts to embed
    texts_to_embed = [chunk["text"] for chunk in all_chunks]
    
    # Initialize sentence-transformers model
    print("Loading Sentence Transformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings...")
    embeddings = model.encode(texts_to_embed, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    # Create and populate FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save FAISS Index
    index_path = os.path.join(vector_dir, "index.faiss")
    faiss.write_index(index, index_path)
    print(f"FAISS index successfully saved to: {index_path}")
    
    # Save mapping metadata (text + source/heading details)
    metadata_path = os.path.join(vector_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=4)
    print(f"Metadata mapping successfully saved to: {metadata_path}")
    print("Ingestion pipeline completed successfully.")
    return True

if __name__ == "__main__":
    success = ingest_documents()
    sys.exit(0 if success else 1)