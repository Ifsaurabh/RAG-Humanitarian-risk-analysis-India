# imports --------------------------------------------------------
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import json
from datetime import datetime, timezone
import boto3


# setup ------------------------------------------------------
load_dotenv()
pine_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# security
security = HTTPBasic()
correct_username = os.getenv("BASIC_AUTH_USERNAME")
correct_password = os.getenv("BASIC_AUTH_PASSWORD")

# verify credentials
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if correct_username is None or correct_password is None:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: auth credentials not set"
        )
    if not secrets.compare_digest(credentials.username, correct_username) or \
       not secrets.compare_digest(credentials.password, correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials

# embedding model ------------------------------------------------------
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# index setup ------------------------------------------------------
pine_index = pine_client.Index("humanitarian-risk")

# FastAPI app instance ------------------------------------------------------
app = FastAPI(
    title="Humanitarian Risk Pinecone",
    description="Analyzing humanitarian risks in India using Pinecone and Anthropic",
    version="1.0.0"
)

# LLM setup ----------------------------------------------------------
llm = ChatAnthropic(model="claude-haiku-4-5-20251001")


# conversation history --------------------------------------------------
chat_history= []

# Request body schema ----------------------------------------------------
class Question(BaseModel):
    question: str
    
# Loading vectors back from Pinecone -------------------------------------
def retrieve_context(question):
    query_embedding = embed_model.encode(question).tolist()

    food_results = pine_index.query(
        vector=query_embedding,
        namespace="food_prices",
        top_k=9,
        include_metadata=True
    )

    poverty_results = pine_index.query(
        vector=query_embedding,
        namespace="poverty_mpi",
        top_k=9,
        include_metadata=True
    )
    
    food_texts= [match['metadata']['text'] for match in food_results['matches']]
    poverty_texts = [match['metadata']['text'] for match in poverty_results['matches']]
    all_texts = food_texts + poverty_texts
    context = "\n\n".join(all_texts)
    return context

# RAG Pipeline ----------------------------------------------------------
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

# logging report to s3 as local folder
LOG_FILE_PATH = "../logs/qa_log.jsonl"
S3_BUCKET = "my-test-bucket9966"
S3_KEY = "rag-qa-logs/qa_log.jsonl"

def log_interaction(question, answer):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer
    }

    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # append locally
    with open(LOG_FILE_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # upload full file to S3 (overwrites previous version each time)
    try:
        s3_client = boto3.client("s3")
        s3_client.upload_file(LOG_FILE_PATH, S3_BUCKET, S3_KEY)
    except Exception as e:
        print(f"S3 upload failed: {e}")  # don't crash the request over a logging failure

# Health check endpoint ------------------------------------------------
@app.get("/")
def root():
    return {"status": "Humanitarian RAG API is running"}

# Main endpoint ----------------------------------------------------
@app.post("/ask")
def ask_endpoint(body: Question, credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)
    answer = ask(body.question)
    log_interaction(body.question, answer)
    return {
        "question": body.question,
        "answer": answer
    }

