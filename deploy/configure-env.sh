#!/bin/bash

# Environment Configuration Helper for Azure Deployment

echo "Environment Configuration Helper"
echo "=================================="
echo ""
echo "This script will help you configure environment variables for your Azure deployment."
echo "You'll need to have your Azure service credentials ready."
echo ""

# Configuration
RESOURCE_GROUP="nestle-chatbot-rg"

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
    read -p "Enter the backend app name you want to configure: " BACKEND_APP_NAME
fi

# Function to prompt for input
prompt_for_value() {
    local var_name=$1
    local description=$2
    local current_value=$3
    
    echo ""
    echo "$description"
    if [ ! -z "$current_value" ]; then
        echo "   Current value: $current_value"
    fi
    read -p "   Enter value: " value
    echo "$value"
}

echo "Please provide the following Azure service credentials:"
echo ""

# Azure OpenAI Configuration
echo "Azure OpenAI Configuration"
echo "------------------------------"
AZURE_OPENAI_ENDPOINT=$(prompt_for_value "AZURE_OPENAI_ENDPOINT" "Azure OpenAI Endpoint (e.g., https://your-openai.openai.azure.com/)")
AZURE_OPENAI_API_KEY=$(prompt_for_value "AZURE_OPENAI_API_KEY" "Azure OpenAI API Key")
AZURE_OPENAI_DEPLOYMENT=$(prompt_for_value "AZURE_OPENAI_DEPLOYMENT" "Azure OpenAI Deployment Name (e.g., gpt-4)")

# Azure Embedding Configuration
echo ""
echo "Azure Embedding Configuration"
echo "--------------------------------"
AZURE_EMBEDDING_ENDPOINT=$(prompt_for_value "AZURE_EMBEDDING_ENDPOINT" "Azure Embedding Endpoint (can be same as OpenAI)" "$AZURE_OPENAI_ENDPOINT")
AZURE_EMBEDDING_API_KEY=$(prompt_for_value "AZURE_EMBEDDING_API_KEY" "Azure Embedding API Key (can be same as OpenAI)" "$AZURE_OPENAI_API_KEY")
AZURE_EMBEDDING_DEPLOYMENT=$(prompt_for_value "AZURE_EMBEDDING_DEPLOYMENT" "Azure Embedding Deployment Name (e.g., text-embedding-ada-002)")

# Azure Search Configuration
echo ""
echo "Azure AI Search Configuration"
echo "--------------------------------"
AZURE_SEARCH_ENDPOINT=$(prompt_for_value "AZURE_SEARCH_ENDPOINT" "Azure Search Endpoint (e.g., https://your-search.search.windows.net)")
AZURE_SEARCH_ADMIN_KEY=$(prompt_for_value "AZURE_SEARCH_ADMIN_KEY" "Azure Search Admin Key")
AZURE_SEARCH_INDEX_NAME=$(prompt_for_value "AZURE_SEARCH_INDEX_NAME" "Azure Search Index Name" "nestle-content-index")

# Azure Cosmos DB Configuration
echo ""
echo "Azure Cosmos DB Configuration"
echo "--------------------------------"
AZURE_COSMOS_ENDPOINT=$(prompt_for_value "AZURE_COSMOS_ENDPOINT" "Azure Cosmos DB Endpoint (e.g., https://your-cosmos.documents.azure.com:443/)")
AZURE_COSMOS_KEY=$(prompt_for_value "AZURE_COSMOS_KEY" "Azure Cosmos DB Primary Key")
AZURE_COSMOS_DATABASE_NAME=$(prompt_for_value "AZURE_COSMOS_DATABASE_NAME" "Cosmos DB Database Name" "nestle-graph-db")

echo ""
echo "Configuring Azure App Service..."

# Configure all environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $BACKEND_APP_NAME \
  --settings \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
    AZURE_OPENAI_API_VERSION="2024-02-01" \
    AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
    AZURE_EMBEDDING_ENDPOINT="$AZURE_EMBEDDING_ENDPOINT" \
    AZURE_EMBEDDING_API_KEY="$AZURE_EMBEDDING_API_KEY" \
    AZURE_EMBEDDING_API_VERSION="2024-02-01" \
    AZURE_EMBEDDING_MODEL_NAME="text-embedding-ada-002" \
    AZURE_EMBEDDING_DEPLOYMENT="$AZURE_EMBEDDING_DEPLOYMENT" \
    AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
    AZURE_SEARCH_ADMIN_KEY="$AZURE_SEARCH_ADMIN_KEY" \
    AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
    AZURE_SEARCH_API_VERSION="2024-07-01" \
    AZURE_COSMOS_ENDPOINT="$AZURE_COSMOS_ENDPOINT" \
    AZURE_COSMOS_KEY="$AZURE_COSMOS_KEY" \
    AZURE_COSMOS_DATABASE_NAME="$AZURE_COSMOS_DATABASE_NAME" \
    AZURE_COSMOS_ENTITIES_CONTAINER_NAME="entities" \
    AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME="relationships" \
  --output table

echo ""
echo "✅ Environment variables configured successfully!"
echo ""
echo "Restarting the app to apply changes..."
az webapp restart --resource-group $RESOURCE_GROUP --name $BACKEND_APP_NAME

echo ""
echo "Configuration completed!"
echo "Your backend should now be properly configured with all Azure services."
echo ""
echo "Backend URL: https://$BACKEND_APP_NAME.azurewebsites.net"
echo ""
echo "Next steps:"
echo "1. Test your backend: curl https://$BACKEND_APP_NAME.azurewebsites.net/"
echo "2. Configure your frontend environment variables"
echo "3. Deploy your frontend to Azure Static Web Apps" 