// API URLs
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL,
  wsURL: import.meta.env.VITE_WS_URL,
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

// API endpoints
export const ENDPOINTS = {
  // Chat endpoints
  CHAT: '/chat',
  CHAT_SEARCH: '/chat/search',
  CHAT_RECIPES: '/chat/recipes',
  CHAT_PRODUCTS: '/chat/products',
  CHAT_COOKING_TIPS: '/chat/cooking-tips',
  CHAT_NUTRITION: '/chat/nutrition',
  CHAT_QUICK_SEARCH: '/chat/quick-search',
  CHAT_HEALTH: '/chat/health',
  CHAT_EXAMPLES: '/chat/examples',
  
  // WebSocket endpoints
  WS: '/ws',
  WS_CONVERSATION: '/ws/{conversationId}',
};

// Request configuration
export const REQUEST_CONFIG = {
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
};

export default API_CONFIG; 