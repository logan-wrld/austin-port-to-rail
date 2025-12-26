__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import subprocess
import time
import requests
import atexit
import signal
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM

# Ollama server process handle
ollama_process = None

def check_ollama_running(host="http://localhost:11434"):
    """Check if Ollama server is already running."""
    try:
        response = requests.get(f"{host}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama_server():
    """Start Ollama server as a subprocess."""
    global ollama_process
    
    if check_ollama_running():
        print("✓ Ollama server already running")
        return True
    
    print("Starting Ollama server...")
    try:
        # Start ollama serve in background
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from terminal signals
        )
        
        # Wait for server to be ready
        max_attempts = 30
        for i in range(max_attempts):
            if check_ollama_running():
                print(f"✓ Ollama server started (pid: {ollama_process.pid})")
                return True
            time.sleep(1)
            if i % 5 == 4:
                print(f"  Waiting for Ollama... ({i+1}s)")
        
        print("✗ Ollama server failed to start within timeout")
        return False
        
    except FileNotFoundError:
        print("✗ Ollama not found. Install from https://ollama.ai")
        return False
    except Exception as e:
        print(f"✗ Failed to start Ollama: {e}")
        return False

def stop_ollama_server():
    """Stop the Ollama server if we started it."""
    global ollama_process
    if ollama_process:
        print("\nStopping Ollama server...")
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
            print("✓ Ollama server stopped")
        except subprocess.TimeoutExpired:
            ollama_process.kill()
            print("✓ Ollama server killed")
        ollama_process = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    stop_ollama_server()
    sys.exit(0)

# Register cleanup handlers
atexit.register(stop_ollama_server)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start Ollama server
if not start_ollama_server():
    print("Cannot continue without Ollama server")
    sys.exit(1)

# Embeddings (must match indexing)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load DB
db = Chroma(
    persist_directory="./chroma",
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k": 4})

# Local 1.5B model
llm = OllamaLLM(model="qwen2.5:1.5b")

def query_data(question):
    """Query the indexed data and return an answer."""
    print(f"\nSearching for: {question}")
    print("-" * 50)
    
    # Retrieve relevant documents
    docs = retriever.invoke(question)
    
    # Build context from retrieved documents
    context = "\n\n".join(d.page_content for d in docs)
    
    # Show source files
    source_files = set(d.metadata.get("source_file", "unknown") for d in docs)
    print(f"Found {len(docs)} relevant documents from: {', '.join(source_files)}")
    print("-" * 50)
    
    # Create prompt
    prompt = f"""You are answering questions about Austin port-to-rail logistics data. You MUST look at and use the dataset provided below to answer the question. Only use information that is present in the dataset. If the dataset does not contain enough information to answer the question, say so explicitly.

Dataset (from CSV files):
{context}

Question:
{question}

Based on the dataset above, provide a clear and accurate answer:"""
    
    # Get answer from LLM
    answer = llm.invoke(prompt)
    print(f"\nAnswer:\n{answer}\n")
    return answer

# Interactive query loop
if __name__ == "__main__":
    print("Austin Port-to-Rail Data Query System")
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        query = input("Enter your question: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        try:
            query_data(query)
        except Exception as e:
            print(f"Error: {e}\n")
