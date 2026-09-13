# JanSevaAI — AI Bureaucracy Copilot 🏛️🤖

> **An Autonomous, Agentic AI Bureaucracy Copilot and Citizen Welfare Discovery Platform** — powered by **FastAPI**, **LangGraph multi-agent orchestration**, **ChromaDB RAG**, **Playwright autonomous browser execution**, and **React 18 with TypeScript**.

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated_Browser-45ba4b.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Problem Statement & Overview
Navigating government welfare schemes in India is notoriously cumbersome. Citizens face confusing eligibility rules, disjointed departmental portals, document upload hurdles, and mandatory identity verification (OTP, CAPTCHA).

**JanSevaAI** automates this entire lifecycle:
1. **Demographic Discovery:** Automatically filters central & state schemes based on age, gender, state, and income.
2. **Grounded RAG Knowledge Assistant:** Answers scheme policy queries with 100% citation grounding (cosine similarity thresholding) and direct official portal actions.
3. **Dynamic Form & Document Verification:** Analyzes requirements on the fly, dynamically generates form fields with citizen profile pre-fill, and verifies uploaded documents.
4. **Autonomous Human-in-the-Loop Browser Filing:** Uses Playwright to automatically launch, navigate, and fill out real/mock government portals, seamlessly pausing for human verification (Aadhaar OTP / CAPTCHA) and synchronizing progress in real time.

---

## 🏛️ System Architecture

`
                                  [ Citizen User ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Main Copilot Frontend ]                      [ Mock Government Portal ]
     (React 18 + TS + Vite :5173)                   (React + Vite :5174)
                 │                                               ▲
                 │ (JWT Bearer Auth)                             │ (Automated Filing & HITL)
                 ▼                                               │
     [ FastAPI Backend Core :8000 ]                              │
                 │                                               │
     ┌───────────┼───────────────────────────┐                   │
     ▼           ▼                           ▼                   │
[ PostgreSQL ] [ ChromaDB Vector Store ] [ LangGraph Agents ]────┘
(User Auth)    (Grounded Policy RAG)        │
                                            ├─ Discovery Agent
                                            ├─ Knowledge Agent
                                            ├─ Document Agent
                                            └─ Playwright Browser Worker
`

---

## 🚀 Key Features & Highlights

- 🔐 **JWT Authentication & Scoping:** Full Signup/Login flow backed by PostgreSQL & bcrypt password hashing.
- 🎯 **Demographic Eligibility Engine:** Deterministic scheme filtering across Indian states and Union Territories.
- 📚 **Hallucination-Free RAG:** ChromaDB vector store + local embeddings (
omic-embed-text / SentenceTransformers) with strict cosine distance guardrails.
- 📑 **Dynamic Form Generation:** Forms render dynamically based on scheme-specific metadata with instant pre-fill.
- 🤖 **Playwright Autonomous Agent (HITL):** Launches full-screen Chromium (--start-maximized, 
o_viewport=True), fills academic/personal info, and yields control back to citizen for OTP/CAPTCHA.
- 🔄 **Bidirectional Synchronization:** Real-time webhook callbacks update application status from external portals into the copilot workflow without manual polling delay.
- 🎨 **Indian DPI Government Portal UI:** Ashoka Navy & Heritage Gold design tokens, accessible layouts, tricolor branding, and full modal scroll-locking.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework:** FastAPI (Python 3.13)
- **Database:** PostgreSQL (with SQLite fallback) + SQLAlchemy 2.0 ORM
- **Authentication:** PyJWT (HS256) + Passlib (bcrypt)
- **Multi-Agent Orchestration:** LangGraph (StateGraph), LangChain
- **Vector Database & RAG:** ChromaDB, SentenceTransformers (ll-MiniLM-L6-v2) / Ollama (
omic-embed-text, llama3.2)
- **Browser Automation:** Playwright (Chromium)
- **Testing:** Pytest (96 automated tests)

### **Frontend**
- **Library:** React 18 with TypeScript
- **Bundler:** Vite 5
- **State Management:** React Context API (AuthContext)
- **Design:** Custom CSS3 Design System with DPI Government portal theme tokens (gov-theme.css)

---

## 📂 Project Structure

`
ai-bureaucracy-copilot/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph Multi-Agent Workflows
│   │   ├── api/             # FastAPI Endpoints (auth, schemes, automation, rag)
│   │   ├── core/            # Security, config, dependencies
│   │   ├── db/              # PostgreSQL models & session setup
│   │   ├── models/          # Pydantic domain models
│   │   ├── schemas/         # Request / Response validation schemas
│   │   └── services/        # Business logic & Playwright browser workers
│   ├── data/                # Vector store & sample schemes dataset
│   ├── tests/               # 96 automated unit & integration tests
│   ├── requirements.txt     # Python backend dependencies
│   └── .env.example         # Backend environment configuration template
│
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/      # UI components (Forms, KnowledgeBox, Modal)
│   │   ├── context/         # AuthContext provider
│   │   ├── pages/           # Discovery, Profile, Login, Signup pages
│   │   └── styles/          # Government design system & tokens
│   ├── package.json
│   └── vite.config.ts
│
├── mock-portal/             # Simulated Government Portal (e.g., Vidya Lakshmi)
│   ├── backend/             # Lightweight mock portal server (:8001)
│   └── frontend/            # Multi-step government portal application (:5174)
│
├── docker-compose.yml       # PostgreSQL container setup
├── start_all.bat            # One-click startup script for all services
└── README.md
`

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL (or Docker to run PostgreSQL)

### 1. Clone Repository
`ash
git clone https://github.com/<your-username>/ai-bureaucracy-copilot.git
cd ai-bureaucracy-copilot
`

### 2. Configure Environment Variables
`ash
# Backend configuration
cp backend/.env.example backend/.env
`
*(Update DATABASE_URL in ackend/.env with your PostgreSQL credentials, or use the Docker command below).*

To start a local PostgreSQL instance with Docker:
`ash
docker-compose up -d
`

### 3. Install Dependencies & Build Index
`ash
# Setup Backend
cd backend
python -m pip install -r requirements.txt
python -m playwright install chromium

# Build vector index
python -m app.scripts.build_index

# Setup Frontend
cd ../frontend
npm install

# Setup Mock Portal Frontend
cd ../mock-portal/frontend
npm install
`

### 4. Run the Full Stack
You can start everything via the included batch script (Windows):
`ash
start_all.bat
`
Or start services individually in separate terminals:
- **FastAPI Core Backend:** cd backend && python -m uvicorn app.main:app --reload --port 8000
- **Citizen Copilot Frontend:** cd frontend && npm run dev → http://localhost:5173
- **Mock Portal Backend:** cd mock-portal/backend && python -m uvicorn main:app --reload --port 8001
- **Mock Portal Frontend:** cd mock-portal/frontend && npm run dev -- --port 5174 → http://localhost:5174

---

## 🧪 Running Automated Tests

Run the complete test suite (96 tests) across authentication, scheme discovery, demographic filtering, RAG grounding, and portal automation:
`ash
cd backend
python -m pytest tests/
`

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
