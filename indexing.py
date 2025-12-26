__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Get all CSV files from data folder
data_folder = "data"
csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]

print(f"Found {len(csv_files)} CSV files to process...")

# Process each CSV file
all_documents = []

for csv_file in csv_files:
    file_path = os.path.join(data_folder, csv_file)
    print(f"Processing {csv_file}...")
    
    try:
        # Try reading with comma separator first
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except:
            # If that fails, try tab separator
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        
        # Convert each row to a text document
        for idx, row in df.iterrows():
            # Create a readable text representation of the row
            row_text_parts = []
            for col, val in row.items():
                if pd.notna(val):  # Only include non-null values
                    row_text_parts.append(f"{col}: {val}")
            
            row_text = ", ".join(row_text_parts)
            
            # Create document with metadata
            doc = Document(
                page_content=row_text,
                metadata={
                    "source_file": csv_file,
                    "row_index": idx,
                    "file_type": "csv"
                }
            )
            all_documents.append(doc)
        
        print(f"  Added {len(df)} rows from {csv_file}")
    
    except Exception as e:
        print(f"  Error processing {csv_file}: {str(e)}")
        continue

print(f"\nTotal documents created: {len(all_documents)}")

# Chunk documents
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunked_documents = splitter.split_documents(all_documents)

print(f"Total chunks after splitting: {len(chunked_documents)}")

# Embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Store in Chroma
db = Chroma(
    persist_directory="./chroma",
    embedding_function=embeddings
)

# Add documents in batches to avoid exceeding ChromaDB's batch size limit
batch_size = 5000
total_docs = len(chunked_documents)
print(f"Adding {total_docs} documents in batches of {batch_size}...")

for i in range(0, total_docs, batch_size):
    batch = chunked_documents[i:i + batch_size]
    db.add_documents(batch)
    print(f"  Added batch {i//batch_size + 1} ({len(batch)} documents)")

print("Indexing complete! Data stored in ./chroma")
