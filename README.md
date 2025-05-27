# Nestlé AI Chatbot

An AI-based chatbot for the Made with Nestlé website that can handle user queries, generate appropriate responses, and provide reference links where necessary.

## Quick Deployment

Deploy your full-featured Nestle AI Chatbot to Azure with all advanced capabilities:

```bash
cd deploy

# 1. Deploy infrastructure and backend
./deploy.sh

# 2. Configure environment variables
./configure-env.sh

# 3. Deploy frontend
./deploy-frontend.sh
```

## Tech Stack

### Backend
- **Language**: Python
- **Framework**: FastAPI
- **Services**: 
  - Azure OpenAI (GPT-4 & Embeddings)
  - Azure AI Search (Vector Database)
  - Azure Cosmos DB (Graph Database)
  - Playwright (Web Scraping)

### Frontend
- **Language**: JavaScript
- **Framework**: Vite + React
- **UI Library**: Material-UI

### Cloud Infrastructure
- **Platform**: Azure
- **Backend**: Azure App Service
- **Frontend**: Azure Static Web Apps

## Features

- **AI-Powered Chat**: GPT-4 powered responses with context awareness
- **Semantic Search**: Vector-based search across Nestlé content
- **GraphRAG**: Graph-enhanced retrieval for better context
- **Responsive UI**: Modern, mobile-friendly interface
- **Real-time**: WebSocket support for instant responses
- **Rich Content**: Support for recipes, products, and brand information

## Project Structure
```
nestle-ai-chatbot/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── chat/           # Chat endpoints and logic
│   │   ├── search/         # Vector search implementation
│   │   ├── graph/          # GraphRAG implementation
│   │   └── scrape/         # Web scraping utilities
│   ├── config/             # Configuration files
│   ├── startup.py          # Azure deployment entry point
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── config/         # Configuration
│   └── package.json
├── deploy/                # Deployment scripts and guides
│   ├── deploy.sh          # Main deployment script with region selection
│   ├── configure-env.sh   # Environment configuration helper
│   ├── deploy-frontend.sh # Frontend deployment script
│   └── deploy-azure.md    # Detailed deployment guide
├── scripts/               # Development and utility scripts
│   ├── start.sh          # Local development startup script
│   ├── scrape/           # Web scraping scripts
│   ├── search/           # Search indexing scripts
│   └── graph/            # Graph database scripts
├── data/                 # Data storage
│   ├── raw/              # Raw scraped data
│   └── processed/        # Processed data for indexing
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure account with OpenAI, Search, and Cosmos DB services

### Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# Start both services
cd .. && ./scripts/start.sh
```

### Environment Variables

#### Backend:
```env
# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_ADMIN_KEY="your-search-admin-key"
AZURE_SEARCH_INDEX_NAME="nestle-ai-chatbot-index"
AZURE_SEARCH_API_VERSION="2024-07-01"

# Azure Embedding Model Configuration
AZURE_EMBEDDING_ENDPOINT="https://your-openai-service.openai.azure.com"
AZURE_EMBEDDING_API_KEY="your-embedding-api-key"
AZURE_EMBEDDING_API_VERSION="2023-05-15"
AZURE_EMBEDDING_MODEL_NAME="text-embedding-3-small"
AZURE_EMBEDDING_DEPLOYMENT="text-embedding-3-small"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://your-openai-service.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
AZURE_OPENAI_API_KEY="your-openai-api-key"
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
AZURE_OPENAI_DEPLOYMENT="gpt-4o"

# Azure Cosmos DB Configuration
AZURE_COSMOS_ENDPOINT="https://your-cosmos-db.documents.azure.com:443/"
AZURE_COSMOS_KEY="your-cosmos-db-key"
AZURE_COSMOS_DATABASE_NAME="nestle-ai-chatbot-cosmos"
AZURE_COSMOS_ENTITIES_CONTAINER_NAME="nestle-ai-chatbot-entities"
AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME="nestle-ai-chatbot-relationships"
```

#### Frontend:
```env
# API endpoints (for local development)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```
