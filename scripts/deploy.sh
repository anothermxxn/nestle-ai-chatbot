#!/bin/bash

# Nestle AI Chatbot Deployment Script
# This script builds Docker images and deploys them to Azure Container Apps

set -e  # Exit on any error

source .env
echo "Loaded environment variables from .env"

# Image names and tags
BACKEND_IMAGE="${REGISTRY_LOGIN_SERVER}/nestle-backend"
FRONTEND_IMAGE="${REGISTRY_LOGIN_SERVER}/nestle-frontend"
TAG=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        log_error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    # Check if Azure resources exist
    if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
        log_error "Resource group $RESOURCE_GROUP does not exist."
        exit 1
    fi
    
    # Check if registry credentials are provided
    if [ -z "$REGISTRY_LOGIN_SERVER" ] || [ -z "$REGISTRY_USERNAME" ] || [ -z "$REGISTRY_PASSWORD" ]; then
        log_error "Registry credentials not found in .env file. Please add REGISTRY_LOGIN_SERVER, REGISTRY_USERNAME, and REGISTRY_PASSWORD."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

login_to_registry() {
    log_info "Logging into Azure Container Registry..."
    if echo $REGISTRY_PASSWORD | docker login $REGISTRY_LOGIN_SERVER --username $REGISTRY_USERNAME --password-stdin; then
        log_success "Successfully logged into ACR!"
    else
        log_error "Failed to login to ACR. Please check your credentials."
        exit 1
    fi
}

build_backend_image() {
    log_info "Building backend Docker image..."
    
    cd ../backend
    
    # Build the image
    if docker build -t $BACKEND_IMAGE:$TAG -t $BACKEND_IMAGE:latest .; then
        log_success "Backend image built successfully!"
    else
        log_error "Failed to build backend image"
        exit 1
    fi
    
    cd ../scripts
}

build_frontend_image() {
    log_info "Building frontend Docker image..."
    
    cd ../frontend
    
    # Build the image
    if docker build -t $FRONTEND_IMAGE:$TAG -t $FRONTEND_IMAGE:latest .; then
        log_success "Frontend image built successfully!"
    else
        log_error "Failed to build frontend image"
        exit 1
    fi
    
    cd ../scripts
}

push_images() {
    log_info "Pushing images to Azure Container Registry..."
    
    # Push backend images
    log_info "Pushing backend image..."
    if docker push $BACKEND_IMAGE:$TAG && docker push $BACKEND_IMAGE:latest; then
        log_success "Backend images pushed successfully!"
    else
        log_error "Failed to push backend images"
        exit 1
    fi
    
    # Push frontend images
    log_info "Pushing frontend image..."
    if docker push $FRONTEND_IMAGE:$TAG && docker push $FRONTEND_IMAGE:latest; then
        log_success "Frontend images pushed successfully!"
    else
        log_error "Failed to push frontend images"
        exit 1
    fi
    
    log_success "All images pushed successfully!"
}

update_container_apps() {
    log_info "Updating Azure Container Apps..."
    
    # Update backend container app
    log_info "Updating backend container app..."
    if az containerapp update \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $BACKEND_IMAGE:$TAG \
        --output table; then
        log_success "Backend container app updated successfully!"
    else
        log_error "Failed to update backend container app"
        exit 1
    fi
    
    # Update frontend container app
    log_info "Updating frontend container app..."
    if az containerapp update \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $FRONTEND_IMAGE:$TAG \
        --output table; then
        log_success "Frontend container app updated successfully!"
    else
        log_error "Failed to update frontend container app"
        exit 1
    fi
    
    log_success "Container apps updated successfully!"
}

get_app_urls() {
    log_info "Getting application URLs..."
    
    BACKEND_URL=$(az containerapp show \
        --name $BACKEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    FRONTEND_URL=$(az containerapp show \
        --name $FRONTEND_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    echo ""
    echo "================================"
    log_success "Deployment completed successfully!"
    echo "================================"
    echo ""
    echo "Application URLs:"
    echo "Backend API:  https://$BACKEND_URL"
    echo "Frontend App: https://$FRONTEND_URL"
    echo ""
    echo "Image Tags Used:"
    echo "Backend:  $BACKEND_IMAGE:$TAG"
    echo "Frontend: $FRONTEND_IMAGE:$TAG"
    echo ""
    echo "You can check the deployment status with:"
    echo "az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
    echo "az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
}

rollback() {
    log_warning "Rolling back to previous version..."
    
    echo ""
    echo "To rollback manually, use:"
    echo "# List revisions:"
    echo "az containerapp revision list --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --output table"
    echo "az containerapp revision list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --output table"
    echo ""
    echo "# Activate previous revision:"
    echo "az containerapp revision set-active --revision <previous-revision-name> --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP"
    echo "az containerapp revision set-active --revision <previous-revision-name> --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP"
    echo ""
}

cleanup_old_images() {
    log_info "Cleaning up old local Docker images..."
    
    # Remove untagged images
    docker image prune -f
    
    log_success "Local cleanup completed!"
}

show_help() {
    echo "Nestle AI Chatbot - Azure Container Apps Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h              Show this help message"
    echo "  --build-only           Only build images, don't deploy"
    echo "  --deploy-only          Only deploy (assumes images are already built)"
    echo "  --tag TAG              Use specific tag instead of timestamp"
    echo "  --rollback             Show rollback instructions"
    echo ""
}

main() {
    local build_only=false
    local deploy_only=false
    local show_rollback=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --build-only)
                build_only=true
                shift
                ;;
            --deploy-only)
                deploy_only=true
                shift
                ;;
            --tag)
                TAG="$2"
                shift 2
                ;;
            --rollback)
                show_rollback=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [[ $show_rollback == true ]]; then
        rollback
        exit 0
    fi
    
    echo "================================"
    echo "Nestle AI Chatbot Deployment"
    echo "================================"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Registry: $REGISTRY_LOGIN_SERVER"
    echo "Timestamp: $(date)"
    echo "Tag: $TAG"
    echo "================================"
    echo ""
    
    check_prerequisites
    
    if [[ $deploy_only == false ]]; then
        login_to_registry
        build_backend_image
        build_frontend_image
        push_images
    fi
    
    if [[ $build_only == false ]]; then
        update_container_apps
        get_app_urls
    fi
    
    if [[ $build_only == false && $deploy_only == false ]]; then
        cleanup_old_images
    fi
    
    log_success "Script completed successfully!"
}

# Trap to handle interruption
trap 'log_error "Script interrupted!"; exit 1' INT TERM

# Run main function
main "$@" 