# Azure App Service Deployment Guide

## Prerequisites

1. **Azure VS Code Extension**: Install the Azure App Service extension in VS Code
2. **Azure Account**: Ensure you're logged into your Azure account in VS Code
3. **Python Runtime**: Azure App Service will use Python 3.11 (specified in `runtime.txt`)

## Deployment Files

The following files are configured for Azure App Service deployment:

### Core Files
- `app.py` - **Primary entry point** for Azure App Service
- `startup.py` - Alternative startup script
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification (Python 3.11)
- `Procfile` - Process specification
- `test_deployment.py` - Deployment verification script

## Deployment Steps

### Using Azure VS Code Extension

1. **Open VS Code** in your project root directory
2. **Install Azure App Service Extension** if not already installed
3. **Sign in to Azure** using the Azure extension
4. **Right-click on the `backend` folder** in VS Code Explorer
5. **Select "Deploy to Web App..."**
6. **Choose your subscription and resource group**
7. **Create a new Web App** or select existing one:
   - **Runtime**: Python 3.11
   - **Region**: Choose your preferred region
   - **Pricing tier**: Choose appropriate tier

### Important: Folder Selection
- **Always select the `backend` folder** when deploying
- Do NOT select the root project folder
- The backend folder contains all necessary deployment files

## Startup Configuration

Azure App Service will automatically detect and use:

### Primary Startup Command
```bash
python app.py
```

### Alternative Commands (if primary fails)
```bash
python startup.py
# or
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

Azure App Service automatically sets:
- `PORT` - The port your app should listen on
- `PYTHONPATH` - Set automatically by our startup scripts

## Verification

After deployment, you can verify the deployment by:

1. **Check the logs** in Azure portal or VS Code
2. **Visit your app URL** (provided after deployment)
3. **Test the health endpoint**: `https://your-app.azurewebsites.net/health`

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you deployed the `backend` folder, not the root folder
   - Check that `requirements.txt` includes all dependencies

2. **Port Issues**
   - Azure automatically sets the PORT environment variable
   - Our startup scripts handle this automatically

3. **Python Path Issues**
   - Our `app.py` and `startup.py` scripts automatically configure Python paths
   - No manual configuration needed

### Debug Commands

If deployment fails, you can test locally:

```bash
# Test the deployment environment
python test_deployment.py

# Test the main app
python app.py

# Test health check
python health_check.py
```

### Log Analysis

Check Azure App Service logs for:
- Import errors
- Port binding issues
- Missing dependencies
- Python path problems

## File Structure

When deployed, Azure expects this structure:
```
/home/site/wwwroot/
├── app.py              # Primary entry point
├── startup.py          # Alternative entry point
├── requirements.txt    # Dependencies
├── runtime.txt         # Python version
├── Procfile           # Process definition
├── src/               # Source code
│   ├── main.py        # FastAPI app
│   ├── chat/          # Chat modules
│   ├── search/        # Search modules
│   └── ...
├── config/            # Configuration
└── ...
```

## Success Indicators

Deployment is successful when you see:
- ✅ Container started successfully
- ✅ HTTP pings responding on port 8000
- ✅ App accessible via the provided URL
- ✅ Health endpoint returns 200 OK

## Support

If you encounter issues:
1. Check the Azure App Service logs
2. Verify all files are in the `backend` folder
3. Ensure `requirements.txt` is complete
4. Test locally with `python app.py` 