# Multi-Agent AI Customer Support Assistant using RAG and LLMs

A premium, enterprise-grade AI Customer Support portal powered by a **Multi-Agent Orchestration Engine** and **Retrieval-Augmented Generation (RAG)**. 

This project simulates a smart customer support desk for *TechMart Electronics*. The system analyzes incoming user queries, routes them to specialized AI support agents, fetches relevant company documentation from a local vector database, synthesizes a cohesive reply, and handles automatic API failovers between Google Gemini and Groq (Llama 3.3).

---

##  Key Features

*   **Multi-Agent Routing**: A central coordinator analyzes user queries and context history to trigger one or more specialized support agents (`Billing`, `Technical`, `Product & Sales`, `Complaint Resolution`, and `General FAQ`).
*   **Automatic Response Aggregation**: When multiple agents are triggered, a coordinator agent seamlessly merges drafts into a single, cohesive, polite customer response.
*   **Retrieval-Augmented Generation (RAG)**: Uses a local FAISS index and `SentenceTransformers` (`all-MiniLM-L6-v2`) to retrieve matching paragraphs from company manuals, refund guidelines, and warranties.
*   **Failover LLM Architecture**: Centralized LLM client tries **Google Gemini** (`gemini-2.0-flash`) first and automatically fails over to **Groq** (`llama-3.3-70b-versatile`) if Gemini hits rate limits or quota boundaries. If both fail, it falls back to local raw RAG summaries.
*   **Modern Teal & Slate UI**: Responsive Next.js 16 front-end styled with a glassmorphism Slate theme and vibrant Teal accents.
*   **User Session Control**: Full CRUD support for creating and deleting chat sessions, complete with automatic AI-driven chat renaming (like ChatGPT).
*   **Custom Markdown Parsing**: Renders headers, lists, italics, and bold text natively in chat bubbles without third-party dependencies.

---

##  Technology Stack

### Backend
*   **FastAPI**: High-performance Python web framework.
*   **MongoDB**: Stores user credentials, session metadata, and conversation history.
*   **FAISS**: Facebook AI Similarity Search for dense vector retrieval.
*   **Sentence-Transformers**: Embeds documents and queries locally.
*   **Bcrypt & PyJWT**: Secure password hashing and token-based user authentication.

### Frontend
*   **React 19 & Next.js 16**: Modern App Router setup.
*   **Tailwind CSS**: Sleek charcoal and teal styling.

---

##  Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── agents/            # Multi-agent engines (billing, technical, router, etc.)
│   │   │   ├── billing.py
│   │   │   ├── technical.py
│   │   │   ├── product.py
│   │   │   ├── complaint.py
│   │   │   ├── faq.py
│   │   │   ├── router.py      # Classification & aggregation orchestrator
│   │   │   └── llm_client.py  # Gemini & Groq failover router
│   │   ├── database.py        # MongoDB connection and serialization helpers
│   │   ├── config.py          # Environment settings
│   │   ├── main.py            # API Routes (auth, sessions, chat messages)
│   │   └── rag/
│   │       ├── ingest.py      # Knowledge base PDF/Markdown parser and indexer
│   │       └── retriever.py   # FAISS retriever query script
│   ├── vectorstore/           # Pre-compiled FAISS indexes and metadata
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/               # Page routing & styling
│   │   │   ├── page.tsx       # Main support chat portal interface
│   │   │   └── layout.tsx
│   │   └── context/
│   │       └── AuthContext.tsx # Authentication state machine
│   ├── package.json
│   └── next.config.ts
└── knowledge_base/            # TechMart policies (Warranties, Manuals, FAQs)
```

---

##  Configuration Setup

### 1. Backend Configuration
Navigate to the `backend/` folder and create a `.env` file:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# MongoDB Setup
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=customer_support_db

# Security
JWT_SECRET=supersecretjwtkeythatshouldbechanged123!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
```

---

##  Running the Application

### Prerequisites
*   Ensure **MongoDB** is running locally (`mongodb://localhost:27017`).

### 1. Ingest Knowledge Base
Before starting the backend, index the company policy files located in the `knowledge_base/` folder:
```bash
cd backend
python app/rag/ingest.py
```
This parses the markdown/PDF manuals, creates vector embeddings, and saves the index inside the `vectorstore/` folder.

### 2. Start the Backend API
Install dependencies and launch the Uvicorn server:
```bash
# In backend directory
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The API documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Start the Next.js Frontend
Navigate to the `frontend/` folder, install packages, and boot the server:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

##  Agent Flow Architecture

```mermaid
graph TD
    User([Customer Input]) --> Router{Router Orchestrator}
    Router -->|Determines intents| A[Agents Triggered]
    A -->|Intent: Billing| B[Billing Agent]
    A -->|Intent: Technical| C[Technical Agent]
    A -->|Intent: Product| D[Product Agent]
    A -->|Intent: Complaint| E[Complaint Agent]
    A -->|Intent: FAQ| F[FAQ Agent]
    
    B & C & D & E & F -->|Pull context from| RAG[(FAISS Vector Store)]
    B & C & D & E & F -->|Generate drafts| Agg[Response Aggregator]
    
    Agg -->|Synthesizes response| Out([Unified Support Reply])
```

---

##  Failover & Fallback Logic

Each support agent uses a resilient API call handler:
1.  **Google Gemini (`gemini-2.0-flash`)** generates the response using the RAG context.
2.  If Gemini fails (Quota Exceeded `429`, server overload, or billing lock), the engine prints `Attempting Groq failover...` in the backend console.
3.  **Groq (`llama-3.3-70b-versatile`)** takes over transparently and resolves the request within milliseconds.
4.  If both API calls fail (e.g., offline mode), the agent returns a **formatted, structured summary of the raw retrieved documents** to ensure the customer receives the requested info immediately.

---

##  Deployment Guide

### Option A: Containerized Deployment (Docker & Docker Compose)
The easiest way to self-host the entire stack (FastAPI + Next.js + MongoDB) is using Docker Compose.

1. **Create a `docker-compose.yml`** at the project root:
   ```yaml
   version: '3.8'
   services:
     mongodb:
       image: mongo:6.0
       ports:
         - "27017:27017"
       volumes:
         - mongo_data:/data/db
       networks:
         - support_network

     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - GEMINI_API_KEY=${GEMINI_API_KEY}
         - GROQ_API_KEY=${GROQ_API_KEY}
         - MONGODB_URL=mongodb://mongodb:27017
       depends_on:
         - mongodb
       volumes:
         - ./backend/vectorstore:/app/vectorstore
       networks:
         - support_network

     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://localhost:8000
       depends_on:
         - backend
       networks:
         - support_network

   volumes:
     mongo_data:

   networks:
     support_network:
       driver: bridge
   ```
2. **Build and Run the Containers**:
   ```bash
   docker-compose up -d --build
   ```

---

### Option B: Cloud Production Deployment

#### 1. Database: MongoDB Atlas
*   Set up a free database cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
*   Retrieve your database connection URI (e.g., `mongodb+srv://<username>:<password>@cluster.mongodb.net/`).
*   Update `MONGODB_URL` in your backend `.env` variables with this connection string.

#### 2. Backend API: Render / Railway / AWS ECS
*   Deploy the `backend` directory as a Python web service.
*   Set environment variables (`GEMINI_API_KEY`, `GROQ_API_KEY`, `MONGODB_URL`, `JWT_SECRET`).
*   **Startup Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
*   *Note: Make sure to commit your pre-built `backend/vectorstore/` directory or run `python app/rag/ingest.py` as a post-build command so that the FAISS index is loaded into the cloud container.*

#### 3. Frontend Portal: Vercel
*   Deploy the `frontend` directory to [Vercel](https://vercel.com).
*   Set environment variables:
    *   `NEXT_PUBLIC_API_URL` to your live backend API URL (e.g., `https://your-backend-api.onrender.com`).

