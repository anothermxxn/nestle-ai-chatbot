#!/bin/bash

# Frontend Deployment Script for Azure Static Web Apps

echo "Frontend Deployment to Azure Static Web Apps"
echo "==============================================="

# Configuration
RESOURCE_GROUP="nestle-chatbot-rg"
FRONTEND_APP_NAME="nestle-chatbot-frontend"

# Try to find the backend app automatically
echo "Looking for your backend app..."
BACKEND_APPS=$(az webapp list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'nestle-chatbot-backend')].name" --output tsv 2>/dev/null)

if [ -z "$BACKEND_APPS" ]; then
    echo "⚠️ Could not find backend app automatically."
    read -p "Enter your backend app name (e.g., nestle-chatbot-backend-20250527): " BACKEND_APP_NAME
elif [ $(echo "$BACKEND_APPS" | wc -l) -eq 1 ]; then
    BACKEND_APP_NAME=$BACKEND_APPS
    echo "✅ Found backend app: $BACKEND_APP_NAME"
else
    echo "Multiple backend apps found:"
    echo "$BACKEND_APPS"
    read -p "Enter the backend app name you want to use: " BACKEND_APP_NAME
fi

# Navigate to frontend directory
cd ../frontend

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Could not find frontend directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Get backend URL
BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"

echo "Configuring environment variables..."
echo "Backend URL: $BACKEND_URL"

# Create environment file for build
cat > .env.production << EOF
VITE_API_URL=$BACKEND_URL
VITE_WS_URL=wss://${BACKEND_APP_NAME}.azurewebsites.net
EOF

echo "✅ Environment variables configured"

# Build the application
echo "Building the application..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build completed successfully"

# Get the Static Web App URL
FRONTEND_URL=$(az staticwebapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostname" --output tsv 2>/dev/null)

if [ -z "$FRONTEND_URL" ]; then
    echo "⚠️ Static Web App not found. Creating it now..."
    
    az staticwebapp create \
      --name $FRONTEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --location "East US 2" \
      --output table
    
    FRONTEND_URL=$(az staticwebapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostname" --output tsv)
fi

echo "Frontend URL: https://$FRONTEND_URL"

# Configure CORS on backend
echo "Configuring CORS..."
az webapp cors add \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --allowed-origins "https://$FRONTEND_URL" \
  --output table

echo ""
echo "Frontend deployment preparation completed!"
echo "============================================="
echo ""
echo "Built files are in the 'dist' directory"
echo "Frontend URL: https://$FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Next steps to complete deployment:"
echo "1. Go to Azure Portal"
echo "2. Navigate to Static Web Apps > $FRONTEND_APP_NAME"
echo "3. Go to 'Overview' and click 'Manage deployment token'"
echo "4. Use Azure Static Web Apps CLI or GitHub Actions to deploy"
echo ""
echo "Alternative - Manual upload:"
echo "1. Go to Azure Portal > Static Web Apps > $FRONTEND_APP_NAME"
echo "2. Go to 'Functions and APIs' > 'Browse'"
echo "3. Upload the contents of the 'dist' folder"
echo ""
echo "Or use Azure Static Web Apps CLI:"
echo "   npm install -g @azure/static-web-apps-cli"
echo "   swa deploy ./dist --app-name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP" 