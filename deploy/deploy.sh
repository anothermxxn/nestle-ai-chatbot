#!/bin/bash

# Nestle AI Chatbot - Azure Deployment Script with Region Selection

set -e  # Exit on any error

echo "Starting Azure deployment for Nestle AI Chatbot..."
echo "=================================================="

# Configuration
RESOURCE_GROUP="nestle-chatbot-rg"
# Generate unique names using today's date
DATE_SUFFIX=$(date +%Y%m%d)
BACKEND_APP_NAME="nestle-chatbot-backend-${DATE_SUFFIX}"
FRONTEND_APP_NAME="nestle-chatbot-frontend-${DATE_SUFFIX}"
APP_SERVICE_PLAN="nestle-chatbot-plan"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "Please login to Azure first..."
    az login
fi

echo "✅ Azure CLI is ready"

# Let user choose region
echo ""
echo "Choose a region for deployment:"
echo "1. East US 2 (recommended)"
echo "2. West US 2"
echo "3. Central US"
echo "4. West Europe"
echo "5. North Europe"
echo "6. Custom region"
echo ""
read -p "Enter your choice (1-6): " region_choice

case $region_choice in
    1) LOCATION="East US 2" ;;
    2) LOCATION="West US 2" ;;
    3) LOCATION="Central US" ;;
    4) LOCATION="West Europe" ;;
    5) LOCATION="North Europe" ;;
    6) 
        echo "Available regions:"
        az account list-locations --query "[].{Name:name, DisplayName:displayName}" --output table
        read -p "Enter region name: " LOCATION
        ;;
    *) 
        echo "Invalid choice, using East US 2"
        LOCATION="East US 2"
        ;;
esac

echo "Selected region: $LOCATION"

# Create or use existing resource group
echo "Checking resource group..."
if az group show --name $RESOURCE_GROUP &> /dev/null; then
    EXISTING_LOCATION=$(az group show --name $RESOURCE_GROUP --query location --output tsv)
    echo "✅ Resource group already exists in: $EXISTING_LOCATION"
    echo "Using existing location: $EXISTING_LOCATION"
    LOCATION=$EXISTING_LOCATION
else
    echo "Creating new resource group in: $LOCATION"
    az group create --name $RESOURCE_GROUP --location "$LOCATION" --output table
fi

# Check if web app already exists and delete it to avoid conflicts
if az webapp show --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME &> /dev/null; then
    echo "Web app already exists. Deleting to avoid deployment conflicts..."
    az webapp delete --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME
    echo "Waiting for deletion to complete..."
    sleep 15
fi

# Create App Service Plan 
echo "Creating App Service Plan..."

if az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux \
  --output table; then
  
  echo "✅ B1 Basic plan created successfully"
else
  echo "❌ Failed to create App Service Plan in $LOCATION"
  echo "Try a different region or contact Azure support to increase quota"
  exit 1
fi

# Create Backend Web App
echo "Creating Backend Web App..."

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $BACKEND_APP_NAME \
  --runtime "PYTHON|3.11" \
  --output table

# Configure Backend
echo "Configuring Backend..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --settings \
    PYTHON_VERSION=3.11 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    PROJECT=backend \
  --output table

az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --startup-file "backend/startup.py" \
  --output table

echo "Backend configuration completed"

# Configure local Git deployment
echo "Configuring local Git deployment..."

# First, configure deployment credentials
echo "Setting up deployment credentials..."
DEPLOYMENT_USER="nestle-deploy-user"
echo "Please enter a password for deployment user (minimum 8 characters):"
read -s DEPLOYMENT_PASSWORD

# Configure deployment user
az webapp deployment user set \
  --user-name $DEPLOYMENT_USER \
  --password $DEPLOYMENT_PASSWORD

# Configure local Git deployment source
DEPLOYMENT_URL=$(az webapp deployment source config-local-git \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --query url --output tsv)

# Replace 'None' with actual deployment username in the URL
DEPLOYMENT_URL=$(echo $DEPLOYMENT_URL | sed "s/None@/$DEPLOYMENT_USER@/")

echo "Git deployment URL: $DEPLOYMENT_URL"

# Deploy code from local repository
echo "Deploying code from local repository..."

# Go back to project root where the main git repository is
cd ..

# Ensure we're on the main branch and everything is committed
echo "Preparing git repository for deployment..."
git add .
git commit -m "Prepare for Azure deployment" || echo "No changes to commit"

# Add Azure remote if not exists
if ! git remote get-url azure &> /dev/null; then
    git remote add azure $DEPLOYMENT_URL
else
    git remote set-url azure $DEPLOYMENT_URL
fi

echo "Pushing to Azure..."
# Push the entire project, Azure will use the backend folder based on deployment settings
git push azure main --force

cd deploy

# Create Static Web App for Frontend
echo "Creating Frontend Static Web App..."
az staticwebapp create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --location "East US 2" \
  --output table

# Get the URLs
BACKEND_URL="https://${BACKEND_APP_NAME}.azurewebsites.net"
FRONTEND_URL=$(az staticwebapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostname" --output tsv)

echo ""
echo "Deployment completed successfully!"
echo "====================================="
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: https://$FRONTEND_URL"
echo ""
echo "⚠️ IMPORTANT NEXT STEPS:"
echo "1. Configure environment variables for the backend:"
echo "   ./configure-env.sh"
echo ""
echo "2. Deploy frontend:"
echo "   ./deploy-frontend.sh"
echo ""
echo "Share this URL with others: https://$FRONTEND_URL" 