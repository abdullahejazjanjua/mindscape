import os
from langchain_community.llms import Ollama
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, DirectoryLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
import time

class MentalHealthChatbot:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="qwen3:0.6b")
        
        self.llm = Ollama(model="qwen3:0.6b")
        
        self.vector_store = None
        self.retrieval_chain = None
        self.faiss_index_path = "mental_health_faiss_index"  
        
    def load_or_create_knowledge_base(self):
        """Load documents and create vector store or load existing one"""
        print("\nLoading mental health resources...")
        
        if os.path.exists(self.faiss_index_path):
            print("Loading existing FAISS index...")
            self.vector_store = FAISS.load_local(
                self.faiss_index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True 
            )
            return
        
        print("Creating new FAISS index...")
        
        web_loader = WebBaseLoader([
            "https://www.mind.org.uk/information-support/tips-for-everyday-living/student-life/about-student-mental-health/",
            "https://sprc.org/consequences-of-student-mental-health-issues/"
        ])
        
        pdf_docs = []
        if os.path.exists("knowledge_base"):
            pdf_loader = DirectoryLoader("knowledge_base", glob="**/*.pdf", loader_cls=PyPDFLoader)
            pdf_docs = pdf_loader.load()
        
        web_docs = web_loader.load()
        all_docs = web_docs + pdf_docs
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(all_docs[:50]) 
        
        self.vector_store = FAISS.from_documents(splits, self.embeddings)
        self.vector_store.save_local(self.faiss_index_path)
        
    def initialize_chain(self):
        """Initialize the RAG chain with proper greeting handling"""
        prompt_template = """
        You are a mental health assistant for students. You are talking to students who are facing mental health issues. Follow these rules strictly:
        1. For greetings like "hi" or "hello", respond with a simple English greeting
        2. Never show internal thought processes
        3. Always Respond in English for any question
        4. Answer in a polite and kind manner
        
        
        Context: {context}
        
        Question: {input}
        
        Respond only with the appropriate answer:
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        self.retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    def chat_loop(self):
        """Run the terminal chat interface with clean output"""
        print("\n" + "="*50)
        print("Mental Health Chatbot")
        print("Type 'quit' to exit\n")
        print("Initializing...")
        
        self.load_or_create_knowledge_base()
        self.initialize_chain()
        
        print("How can I help you today?")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            if not user_input.strip():
                continue
                
            start_time = time.time()
            try:
                response = self.retrieval_chain.invoke({"input": user_input})
                
                # Clean the response by removing any thought process markers
                clean_answer = response['answer'].split('</think>')[-1].strip()
                clean_answer = clean_answer.replace('<think>', '').strip()
                
                # Print only the clean answer
                print(f"\n{clean_answer}")
                print(f"[Response time: {time.time()-start_time:.1f}s]")
                
            except Exception as e:
                print(f"\nSorry, I encountered an error. Please try again.")

if __name__ == "__main__":
    chatbot = MentalHealthChatbot()
    chatbot.chat_loop()