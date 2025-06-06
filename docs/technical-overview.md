# Technical Overview - Nestle AI Chatbot

## Tools and Frameworks

### Backend Stack
- **Python 3.11** with FastAPI for API development
- **LangChain** for AI application framework
- **Azure OpenAI** (GPT-4o) for conversational AI
- **Azure AI Search** for vector storage and semantic search
- **Azure Cosmos DB** for graph database (entities and relationships)
- **Crawl4AI** for web data extraction

### Frontend Stack
- **React 19** with Vite build tool
- **Material-UI v7** for component library
- **JavaScript/Node.js 18** runtime environment

### Cloud Infrastructure
- **Azure Container Apps** for deployment
- **Azure services** for AI, search, and data storage

## RAG Limitation Solution

### Problem Addressed
Traditional RAG systems struggle with structured counting queries like "How many Nestlé products are listed?" due to their reliance on document retrieval rather than data aggregation.

### Solution: GraphRAG + Intelligent Query Routing
1. **Hybrid Architecture**: Combined Azure AI Search (vector embeddings) with Cosmos DB graph database
2. **Query Classification**: Automatic detection of counting vs. descriptive queries
3. **Smart Routing**: 
   - Counting queries → Direct graph database entity counting
   - Regular queries → Traditional vector search + graph traversal
4. **Real-time Aggregation**: Direct counting from structured entities (brands, products, recipes, topics) stored in graph database

## Assumptions and Limitations

### Current Limitations
- **Performance**: Response times up to 10 seconds for complex purchase assistance queries
- **Data Coverage**: ~10% of website content unavailable due to storage constraints
- **External Dependencies**: Amazon scraping subject to rate limiting
- **Mobile Support**: Portrait orientation only
- **Localization**: English language content exclusively
- **Testing**: No automated testing coverage
- **Content Updates**: Manual intervention required for index updates

### Key Assumptions
- Users primarily seek product information, recipes, and purchase assistance
- Mobile-first usage pattern with geolocation availability
- Azure cloud infrastructure scalability sufficient for expected load

## Potential Improvements

1. **Performance Optimization**: Implement caching layers and query optimization
2. **Comprehensive Testing**: Add unit, integration, and end-to-end test suites
3. **Automated Content Pipeline**: Real-time content synchronization and indexing
4. **Enhanced Mobile Experience**: Landscape orientation support and PWA capabilities