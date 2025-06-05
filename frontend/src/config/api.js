const VITE_ENVIRONMENT = import.meta.env.VITE_ENVIRONMENT;
const VITE_DEV_BACKEND_URL = import.meta.env.VITE_DEV_BACKEND_URL;
const VITE_PROD_BACKEND_URL = import.meta.env.VITE_PROD_BACKEND_URL;

const getBackendURL = () => {
  if (VITE_ENVIRONMENT === 'production' && VITE_PROD_BACKEND_URL) {
    return VITE_PROD_BACKEND_URL;
  }
  return VITE_DEV_BACKEND_URL;
};

const BACKEND_URL = getBackendURL();

if (!BACKEND_URL) {
  console.error('Backend URL is not defined. Check your environment variables.');
}

// API URLs
export const API_CONFIG = {
  baseURL: BACKEND_URL,
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  environment: VITE_ENVIRONMENT,
};

// API endpoints
export const ENDPOINTS = {
  // Chat endpoints
  CHAT: '/chat',
  CHAT_SEARCH: '/chat/search',
  CHAT_QUICK_SEARCH: '/chat/quick-search',
  CHAT_HEALTH: '/chat/health',
  CHAT_EXAMPLES: '/chat/examples',
  
  // Graph endpoints
  GRAPH_HEALTH: '/graph/health',
  GRAPH_ENTITIES: '/graph/entities',
  GRAPH_RELATIONSHIPS: '/graph/relationships',
  GRAPH_SCHEMA_ENTITIES: '/graph/schema/entity-types',
  GRAPH_SCHEMA_RELATIONSHIPS: '/graph/schema/relationship-types',
  GRAPH_VALIDATE_ENTITY: '/graph/validate/entity',
  GRAPH_VALIDATE_RELATIONSHIP: '/graph/validate/relationship',
};

// Request configuration
export const REQUEST_CONFIG = {
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
};

export default API_CONFIG; 