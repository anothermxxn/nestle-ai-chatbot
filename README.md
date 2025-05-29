# Nestle AI Chatbot

An AI-powered chatbot that provides intelligent search capabilities over Nestle content, including recipes, product information, cooking tips, and nutrition guidance.

## Live Demo

Try the live application: **[nestle-ai-chatbot](https://nestle-ai-chatbot-frontend.whitewater-4228c4bc.canadaeast.azurecontainerapps.io/)**

## Technologies and Frameworks

### Backend Technologies
- **Python 3.11+**: Core language
- **FastAPI**: Backend framework
- **LangChain**: AI application framework
- **Uvicorn**: ASGI server for running FastAPI
- **Crawl4AI**: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.

### Frontend Technologies
- **JavaScript**: Core language
- **Node.js 18**:
- **React 19**: Frontend framework
- **Vite**: Build tool
- **WebSocket**: Real-time communication
- **Material-UI v7**: UI library

### Cloud Infrastructure
- **Azure AI Search**: Content indexing, semantic search, and vector storage
- **Azure OpenAI**: GPT models and embedding models for AI responses
- **Azure Cosmos DB**: NoSQL database for graph entities and relationships
- **Azure Container Apps**: Application hosting and deployment
- **Python Virtual Environments**: Local development dependency isolation

## Features
- **AI-Powered Chat**: Natural language conversations powered by GPT-4
- **Nestle Content**: Access to recipes, products, brands, and cooking tips
- **Knowledge Graph**: Customizable connected relationships for comprehensive answers
- **Context Memory**: Remembers conversation history for better responses
- **Real-Time Responses**: Instant messaging with WebSocket support
- **REST API**: Complete API with interactive documentation

## Known Limitations
- **UI Design**: The frontend currently displays as a floating chat button at the bottom right corner of a blank page
- **Language Support**: Currently optimized for English content only
- **Content Updates**: Manual process required to update content index
- **Test Coverage**: No unit tests or end-to-end tests implemented due to time constraints
- **Concurrent Users**: Performance may degrade with high concurrent usage without proper scaling

## Local Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nestle-ai-chatbot
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend

   # Install dependencies
   npm install
   ```

4. **Configuration**
   
   Create `.env` file in the `backend/` directory:
   ```env
   ENVIRONMENT="development"
   DEV_FRONTEND_URL="http://localhost:5173"
   PROD_FRONTEND_URL="PLACEHOLDER"

   # Azure AI Search Configuration
   AZURE_SEARCH_ENDPOINT="PLACEHOLDER"
   AZURE_SEARCH_ADMIN_KEY="PLACEHOLDER"
   AZURE_SEARCH_INDEX_NAME="PLACEHOLDER"
   AZURE_SEARCH_API_VERSION="PLACEHOLDER"

   # Azure Embedding Model Configuration
   AZURE_EMBEDDING_ENDPOINT="PLACEHOLDER"
   AZURE_EMBEDDING_API_KEY="PLACEHOLDER"
   AZURE_EMBEDDING_API_VERSION="PLACEHOLDER"
   AZURE_EMBEDDING_MODEL_NAME = "PLACEHOLDER"
   AZURE_EMBEDDING_DEPLOYMENT = "PLACEHOLDER"

   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT="PLACEHOLDER"
   AZURE_OPENAI_API_KEY="PLACEHOLDER"
   AZURE_OPENAI_API_VERSION="PLACEHOLDER"
   AZURE_OPENAI_DEPLOYMENT="PLACEHOLDER"

   # Azure Cosmos DB Configuration
   AZURE_COSMOS_ENDPOINT="PLACEHOLDER"
   AZURE_COSMOS_KEY="PLACEHOLDER"
   AZURE_COSMOS_DATABASE_NAME="PLACEHOLDER"
   AZURE_COSMOS_ENTITIES_CONTAINER_NAME="PLACEHOLDER"
   AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME="nPLACEHOLDER"
   ```
   
   Create `.env.local` file in the `frontend/` directory:
   ```env
   VITE_ENVIRONMENT="development"
   VITE_DEV_BACKEND_URL="http://localhost:8000"
   VITE_PROD_BACKEND_URL="PLACEHOLDER"
   ```

5. **Resources Setup**

   a) **Scrape and Process Content**
   ```bash
   cd scripts/scrape
   
   # Scrape content from website
   python run_scraper.py
   
   # Process scraped content into chunks
   python process_data.py
   ```

   b) **Create Azure AI Search Index**
   ```bash
   cd scripts/search
   python create_index.py
   ```

   c) **Index Content with Embeddings**
   ```bash
   cd scripts/search
   
   # Generate embeddings and upload to search index
   python setup.py
   ```

   d) **Setup Graph Database**
   ```bash
   cd scripts/graph
   
   # Initialize Cosmos DB containers and populate with entities
   python setup.py
   ```

6. **Run the Application**
   
   Use the provided start script to run both backend and frontend:
   ```bash
   # From the project root directory
   cd scripts
   ./start.sh
   ```
   
   The script will:
   - Check that dependencies are installed
   - Start the backend server
   - Start the frontend server
   - Display status and URLs
   - Handle graceful shutdown with Ctrl+C

## Additional Documentation

For more detailed information:
- **[GraphRAG Integration](./docs/graphrag-integration.md)** - Advanced GraphRAG features
- **[API Specification](./docs/api-specification.yaml)** - Complete OpenAPI documentation
