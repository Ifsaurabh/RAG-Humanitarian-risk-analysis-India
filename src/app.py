# RAG Humanitarian Risk Analysis India — FastAPI Application
# Serves the conversational RAG pipeline as a REST API

# --- Imports ---
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# --- Load environment variables ---
load_dotenv()

# --- FastAPI app instance ---
app = FastAPI(
    title="Humanitarian RAG API",
    description="Ask natural language questions about India food prices and poverty data",
    version="1.0.0"
)

# --- LLM setup ---
llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

# --- Embeddings ---
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- Load ChromaDB collections ---
food_vectorstore = Chroma(
    client=chromadb.PersistentClient("../vectorstore/food_poverty_db/"),
    collection_name="food_prices",
    embedding_function=embeddings
)

poverty_vectorstore = Chroma(
    client=chromadb.PersistentClient("../vectorstore/food_poverty_db/"),
    collection_name="poverty_mpi",
    embedding_function=embeddings
)

food_retriever = food_vectorstore.as_retriever(search_kwargs={"k": 9})
poverty_retriever = poverty_vectorstore.as_retriever(search_kwargs={"k": 9})

# --- Conversation history ---
chat_history = []

# --- Request body schema ---
class Question(BaseModel):
    question: str

# --- Retriever function ---
def retrieve_context(question):
    food_docs = food_retriever.invoke(question)
    poverty_docs = poverty_retriever.invoke(question)
    all_docs = food_docs + poverty_docs
    context = "\n".join([doc.page_content for doc in all_docs])
    return context

# --- RAG pipeline ---
def ask(question):
    if chat_history:
        last_answer = chat_history[-1].content
        enriched_question = f"{question} (Previous context: {last_answer[:200]})"
    else:
        enriched_question = question

    context = retrieve_context(enriched_question)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a humanitarian data analyst assistant.
Answer questions based only on the provided context.
Be precise with numbers and facts.
Always cite specific figures when available.

Context: {context}"""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{question}")
    ])

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "chat_history": chat_history,
        "question": question
    })

    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=response.content))

    return response.content

# --- Health check endpoint ---
@app.get("/")
def root():
    return {"status": "Humanitarian RAG API is running"}

# --- Main endpoint ---
@app.post("/ask")
def ask_endpoint(body: Question):
    answer = ask(body.question)
    return {
        "question": body.question,
        "answer": answer
    }