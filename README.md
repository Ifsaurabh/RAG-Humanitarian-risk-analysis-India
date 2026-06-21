# RAG Humanitarian Risk Analysis — India

Ask questions about India's food prices and poverty in plain English — 
get AI-powered answers backed by 34 years of real humanitarian data.

---

## Demo

![Demo Homepage](assets/Demo_homepage.png)
![Question 1](assets/Demo_question_1.png)
![Question 2](assets/Demo_question_2.png)
![Question 3](assets/Demo_question_3.png)
![Question 4](assets/Demo_question_4.png)

---

## What It Does

- Ingests **205,000+ food price records** across 32 Indian states (1994–2026) and **state-level poverty (MPI) data** from OCHA HDX
- Converts raw data into semantic documents, embeds them into ChromaDB, and retrieves the most relevant context for any question
- Passes retrieved context to Claude (Anthropic) to generate precise, data-backed answers in natural language

---

## Architecture

Raw Data (HDX APIs)
↓
Data Cleaning + Text Conversion (Pandas)
↓
Embeddings (sentence-transformers: all-MiniLM-L6-v2)
↓
Vector Store (ChromaDB)
↓
User Question → Embed → Retrieve → Claude → Answer

---

## Data Sources

- **WFP Food Prices** — 205k retail/wholesale price records, 32 states, 1994–2026
- **OCHA HDX MPI** — State-level multidimensional poverty index, 2005–2019

Both fetched live from [OCHA HDX](https://data.humdata.org)

---

## Tech Stack

- **LLM** — Claude Haiku (Anthropic API)
- **Vector DB** — ChromaDB
- **Embeddings** — sentence-transformers
- **API** — FastAPI + uvicorn
- **Data** — Pandas, Requests
- **Env** — Python 3.11, python-dotenv

---

## Sample Questions You Can Ask

- "Which state has the highest rice prices in 2024?"
- "How has wheat price changed in Bihar over 10 years?"
- "Which states have the worst poverty levels in 2019?"
- "How does food security look in Uttar Pradesh?"
- "Compare poverty between Kerala and Jharkhand"

---

## Known Limitations
- RAG retrieval uses semantic similarity, not exhaustive search.
  Ranking queries (highest/lowest) may not always return the 
  globally correct answer on first retrieval.
  Workaround: Ask follow-up questions or specify the state directly.

## Project Structure

RAG-Humanitarian-risk-analysis-India/
│
├── data/                          # raw and cleaned datasets
├── notebooks/                     # step by step jupyter notebooks
│   ├── 01_data_fetch.ipynb
│   ├── 02_data_processing.ipynb
│   ├── 03_chromadb_ingestion.ipynb
│   ├── 04_rag_pipeline.ipynb
│   ├── 05_conversational_rag.ipynb
│   └── 06_fastapi_endpoint.ipynb
├── src/
│   ├── app.py                     # FastAPI application (ChromaDB version)
│   └── app_pinecone.py            # FastAPI application (Pinecone version — deployed live on EC2)
├── vectorstore/                   # ChromaDB persistent storage
├── .env                           # API keys (never committed)
├── .gitignore
├── requirements.txt
└── README.md

---

## How To Run

> **Note:** This repo contains two versions of the app, kept side by side to 
> showcase both approaches: `app.py` (ChromaDB, local vector store) and 
> `app_pinecone.py` (Pinecone, cloud-hosted — this is the version deployed 
> live on EC2). The steps below run the **ChromaDB version locally**. To run 
> the Pinecone version instead, use `uvicorn app_pinecone:app --reload` in 
> step 6 and set `PINECONE_API_KEY` in your `.env`.

```bash
# 1. Clone the repo
git clone https://github.com/Ifsaurabh/RAG-Humanitarian-risk-analysis-India.git

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Anthropic API key
echo ANTHROPIC_API_KEY=your_key_here > .env

# 5. Run ingestion notebook (one time only — can takes upto several hours on depending upon CPU)
# Open notebooks/03_chromadb_ingestion.ipynb and run all cells

# 6. Run the API
cd src
uvicorn app:app --reload
```
> **Note:** ChromaDB vectorstore files are not included in this repo due to 
> size limits (500MB+). Run the ingestion notebook once to generate them locally.

Then visit `http://localhost:8000/docs` to test via Swagger UI.

---

## Try It Live

A live demo is deployed on AWS EC2 (Docker, port 8001 — offset from the 
default 8000 to avoid colliding with Project 2, which runs on the same EC2 
instance). Since this instance doesn't have an Elastic IP, confirm the 
current public IP before connecting (it changes on instance stop/start).

- **Swagger UI:** `http://<current-ec2-ip>:8001/docs`
- **Username:** `demo`
- **Password:** `demo-humanitarian-2026`

Open the link, click "Authorize" in Swagger UI, enter the credentials above, 
then try the `/ask` endpoint with a question like *"Which state has the 
highest rice prices in 2024?"*

---

## Known Limitations & Production Considerations

- **HTTP only (no TLS):** This demo deployment runs over plain HTTP on a 
  single EC2 instance without a domain name. In production, this would be 
  addressed with a registered domain, Nginx as a reverse proxy, and 
  Let's Encrypt for free TLS certificates (via Certbot). Deferred here to 
  keep the deployment footprint minimal for a portfolio demo — the focus 
  of this project is the RAG/agent architecture, not infra hardening.
- **No Elastic IP:** Public IP changes on instance stop/start since this 
  is a cost-optimized t3.micro setup without a static IP allocation.

  ---

## Author

**Saurabh** — transitioning from data analytics to agentic AI engineering.  
GitHub: https://github.com/Ifsaurabh