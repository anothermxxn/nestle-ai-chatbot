# Nestlé AI Chatbot

An AI-based chatbot for the Made with Nestlé website that can handle user queries, generate appropriate responses, and provide reference links where necessary.

## Tech Stack

### Backend
- **Language**: Python 3.11, Node.js 20
- **Framework**: FastAPI
- **Service**: 
  - Azure OpenAI
  - Playwright
- **Database**:
  - Azure AI Search
  - Azure Cosmos DB

### Frontend
- **Language**: JavaScript
- **Framework**: Vite + React

### Cloud Infrastructure
- **Platform**: Azure

## Project Structure
```
nestle-ai-chatbot/
├── backend/
│   ├── src/
│   ├── tests/
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── assets/
│   │   └── page.js
│   ├── tests/
│   └── public/
├── data/
├── README.md
└── .gitignore
```
