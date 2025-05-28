# Azure App Service Deployment Guide

## Prerequisites

1. **Azure VS Code Extension**: Install the Azure App Service extension in VS Code
2. **Azure Account**: Ensure you're logged into your Azure account in VS Code
3. **Python Runtime**: Azure App Service will use Python 3.11 (specified in `runtime.txt`)

## Deployment Files

The following files are configured for Azure App Service deployment:

### Core Files
- `app.py` - Alternative entry point for Azure
- `startup.py` - Main startup script
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification
- `Procfile` - Process specification (optional)
- `health_check.py` - Health check script

### Startup Commands

Azure App Service will automatically detect and use one of these startup commands:

1. **Primary**: `python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT`
2. **Alternative**: `python startup.py`
3. **Fallback**: `python app.py`

## Deployment Steps

### Using Azure VS Code Extension

1. **Open VS Code** in the `backend` directory
2. **Open Command Palette** (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows)
3. **Run**: `Azure App Service: Deploy to Web App`
4. **Select**: Your subscription and resource group
5. **Choose**: Create new web app or select existing
6. **Configure**:
   - **Runtime**: Python 3.11
   - **OS**: Linux
   - **Pricing Tier**: Choose appropriate tier

### Manual Configuration (if needed)

If automatic detection fails, configure these settings in Azure Portal:

#### Application Settings
```
WEBSITES_PORT=8000
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

#### Startup Command
```
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

Ensure these environment variables are set in Azure App Service:

### Required
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_ADMIN_KEY`
- `AZURE_SEARCH_INDEX_NAME`

### Optional
- `COSMOS_ENDPOINT`
- `COSMOS_KEY`
- `COSMOS_DATABASE_NAME`

## Verification

After deployment:

1. **Check Logs**: View deployment logs in Azure Portal
2. **Test Health**: Visit `https://your-app.azurewebsites.net/` 
3. **Expected Response**:
   ```json
   {
     "status": "healthy",
     "message": "Nestle AI Chatbot API is running"
   }
   ```

## Troubleshooting

### Common Issues

1. **Import Errors**: All imports have been fixed to use absolute paths
2. **Port Issues**: App automatically uses `$PORT` environment variable
3. **Dependencies**: All required packages are in `requirements.txt`

### Debug Commands

Run locally to test:
```bash
# Test imports
python health_check.py

# Test startup
PORT=8000 python startup.py

# Test direct uvicorn
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Log Monitoring

Monitor deployment in Azure Portal:
- **Deployment Center** → **Logs**
- **Log Stream** for real-time logs
- **Application Insights** for detailed monitoring

## File Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI application
│   ├── chat/                # Chat functionality
│   ├── search/              # Search functionality
│   ├── graph/               # Graph operations
│   └── scrape/              # Web scraping
├── config/                  # Configuration files
├── app.py                   # Alternative entry point
├── startup.py               # Main startup script
├── requirements.txt         # Dependencies
├── runtime.txt              # Python version
├── Procfile                 # Process specification
└── health_check.py          # Health verification
```

## Notes

- All relative imports have been converted to absolute imports
- The application is configured for both development and production
- Health checks are available at the root endpoint
- Logs will show detailed startup information 