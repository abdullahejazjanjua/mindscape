import os
from langchain_community.llms import Ollama
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
import time

class MentalHealthChatbot:
    def __init__(self):
        # Initialize embedding model (using local Ollama)
        self.embeddings = OllamaEmbeddings(model="llama2")
        
        # Initialize LLM (local)
        self.llm = Ollama(model="llama2")
        
        # Initialize vector store
        self.vector_store = None
        self.retrieval_chain = None
        
    def load_or_create_knowledge_base(self):
        """Load documents and create vector store"""
        print("\nLoading mental health resources...")
        
        # Example: Mix of web and local PDF sources
        web_loader = WebBaseLoader([
            "https://www.nimh.nih.gov/health/topics",
            "https://www.mentalhealth.gov/basics"
        ])
        
        # Load local PDFs if available
        pdf_docs = []
        if os.path.exists("knowledge_base"):
            pdf_loader = DirectoryLoader("knowledge_base", glob="**/*.pdf", loader_cls=PyPDFLoader)
            pdf_docs = pdf_loader.load()
        
        web_docs = web_loader.load()
        all_docs = web_docs + pdf_docs
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(all_docs[:50])  # Limit for local testing
        
        # Create vector store
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        
    def initialize_chain(self):
        """Initialize the RAG chain"""
        prompt_template = """
        You are a compassionate mental health counselor for students. Respond with:
        - Empathetic understanding
        - Evidence-based advice
        - Crisis resources when needed
        
        Context: {context}
        
        Question: {input}
        
        Always consider:
        1. The student's emotional state
        2. Local campus resources
        3. When to recommend professional help
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        document_chain = create_stuff_documents_chain(self.llm, prompt)# CHECK
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        self.retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    def chat_loop(self):
        """Run the terminal chat interface"""
        print("\n" + "="*50)
        print("Mental Health Chatbot (Local RAG Version)")
        print("Type 'quit' to exit\n")
        print("Initializing... (This may take a minute for first run)")
        
        self.load_or_create_knowledge_base()
        self.initialize_chain()
        
        print("System ready. How can I help you today?")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input.strip():
                continue
                
            start_time = time.time()
            try:
                response = self.retrieval_chain.invoke({"input": user_input})
                print(f"\nBot: {response['answer']}")
                print(f"\n[Response generated in {time.time()-start_time:.1f}s]")
                
                # Show sources if requested
                if "source" in user_input.lower():
                    print("\nRelevant resources used:")
                    for i, doc in enumerate(response["context"]):
                        print(f"\n--- Resource {i+1} ---")
                        print(doc.page_content[:500] + "...")
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try a different question or check your Ollama setup")

if __name__ == "__main__":
    chatbot = MentalHealthChatbot()
    chatbot.chat_loop()