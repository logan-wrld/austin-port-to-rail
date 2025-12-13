from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM

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
