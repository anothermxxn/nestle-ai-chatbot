// Configuration
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
  CHAT_HEALTH: '/chat/health',
  
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

/**
 * HTTP API client class for REST endpoints with session management
 */
class ApiClient {
  constructor() {
    this.baseURL = API_CONFIG.baseURL;
  }

  /**
   * Makes a generic HTTP request with error handling
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<Object>} Response data
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Creates a new conversation session
   * @param {Object} metadata - Optional session metadata
   * @returns {Promise<Object>} Session creation response with session_id
   */
  async createSession(metadata = null) {
    const requestBody = {};
    if (metadata) {
      requestBody.metadata = metadata;
    }
    
    return this.request('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  /**
   * Sends a chat message with session management
   * @param {string} message - User message
   * @param {string} sessionId - Session ID (if null, new session will be created)
   * @param {Object} filters - Optional filters (content_type, brand, keywords, top_search_results)
   * @returns {Promise<Object>} Chat response with session_id
   */
  async sendChatMessage(message, sessionId = null, filters = {}) {
    const requestBody = {
      query: message,
      ...filters,
    };
    
    if (sessionId) {
      requestBody.session_id = sessionId;
    }
    
    return this.request('/chat/search', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  /**
   * Gets conversation history for a session
   * @param {string} sessionId - Session ID
   * @param {number} limit - Maximum number of messages to retrieve
   * @returns {Promise<Object>} Conversation history
   */
  async getConversationHistory(sessionId, limit = 20) {
    return this.request(`/chat/sessions/${sessionId}/history?limit=${limit}`);
  }

  /**
   * Deletes a conversation session
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Deletion response
   */
  async deleteSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Gets session statistics
   * @returns {Promise<Object>} Session statistics
   */
  async getSessionStats() {
    return this.request('/chat/sessions/stats');
  }

  /**
   * Performs a search query with optional filters (legacy method for backward compatibility)
   * @param {string} query - Search query
   * @param {Object} filters - Optional filters (content_type, brand, keywords, top_search_results)
   * @returns {Promise<Object>} Search response
   */
  async searchChat(query, filters = {}) {
    return this.sendChatMessage(query, null, filters);
  }

  /**
   * Checks API health
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    return this.request('/chat/health');
  }
}

// Create singleton instance
const apiClient = new ApiClient();

export default apiClient; 