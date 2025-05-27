/**
 * API client for communicating with the Nestle AI Chatbot backend
 * Handles HTTP requests and WebSocket connections
 */

import { API_CONFIG } from '../config/api';

const API_BASE_URL = API_CONFIG.baseURL;
const WS_BASE_URL = API_CONFIG.wsURL;

/**
 * HTTP API client class for REST endpoints
 */
class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
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
   * Sends a chat message and gets a response
   * @param {string} message - User message
   * @param {string} sessionId - Optional session ID for conversation context
   * @returns {Promise<Object>} Chat response
   */
  async sendChatMessage(message, sessionId = null) {
    const requestBody = {
      query: message,
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
   * Performs a search query with optional filters
   * @param {string} query - Search query
   * @param {Object} filters - Optional filters
   * @returns {Promise<Object>} Search response
   */
  async searchChat(query, filters = {}) {
    return this.request('/chat/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        ...filters,
      }),
    });
  }

  /**
   * Gets recipe suggestions for an ingredient
   * @param {string} ingredient - Ingredient name
   * @returns {Promise<Object>} Recipe response
   */
  async getRecipes(ingredient) {
    return this.request('/chat/recipes', {
      method: 'POST',
      body: JSON.stringify({
        ingredient,
      }),
    });
  }

  /**
   * Gets product information
   * @param {string} productName - Product name
   * @returns {Promise<Object>} Product response
   */
  async getProduct(productName) {
    return this.request('/chat/products', {
      method: 'POST',
      body: JSON.stringify({
        product_name: productName,
      }),
    });
  }

  /**
   * Gets cooking tips for a topic
   * @param {string} topic - Cooking topic
   * @returns {Promise<Object>} Cooking tips response
   */
  async getCookingTips(topic) {
    return this.request('/chat/cooking-tips', {
      method: 'POST',
      body: JSON.stringify({
        topic,
      }),
    });
  }

  /**
   * Gets nutrition information
   * @param {string} foodItem - Food item name
   * @returns {Promise<Object>} Nutrition response
   */
  async getNutrition(foodItem) {
    return this.request('/chat/nutrition', {
      method: 'POST',
      body: JSON.stringify({
        food_item: foodItem,
      }),
    });
  }

  /**
   * Performs a quick search
   * @param {string} query - Search query
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Quick search response
   */
  async quickSearch(query, params = {}) {
    const searchParams = new URLSearchParams({
      q: query,
      ...params,
    });
    
    return this.request(`/chat/quick-search?${searchParams}`);
  }

  /**
   * Checks API health
   * @returns {Promise<Object>} Health status
   */
  async checkHealth() {
    return this.request('/chat/health');
  }

  /**
   * Gets example queries
   * @returns {Promise<Object>} Example queries
   */
  async getExamples() {
    return this.request('/chat/examples');
  }

  /**
   * Creates a new chat session
   * @param {string} sessionId - Optional custom session ID
   * @returns {Promise<Object>} Session creation response
   */
  async createSession(sessionId = null) {
    const requestBody = {};
    if (sessionId) {
      requestBody.session_id = sessionId;
    }
    
    return this.request('/chat/session', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  /**
   * Gets session history
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Session history
   */
  async getSessionHistory(sessionId) {
    return this.request(`/chat/session/${sessionId}`);
  }

  /**
   * Deletes a chat session
   * @param {string} sessionId - Session ID to delete
   * @returns {Promise<Object>} Deletion response
   */
  async deleteSession(sessionId) {
    return this.request(`/chat/session/${sessionId}`, {
      method: 'DELETE',
    });
  }
}

/**
 * WebSocket client class for real-time communication
 */
class WebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
  }

  /**
   * Connects to the WebSocket server
   * @param {string} conversationId - Conversation identifier
   * @returns {Promise<void>}
   */
  async connect(conversationId = null) {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = conversationId 
          ? `${WS_BASE_URL}/ws/${conversationId}`
          : `${WS_BASE_URL}/ws`;
        
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Handles incoming WebSocket messages
   * @param {Object} data - Message data
   */
  handleMessage(data) {
    const { type, ...payload } = data;
    
    if (this.listeners.has(type)) {
      this.listeners.get(type).forEach(callback => {
        try {
          callback(payload);
        } catch (error) {
          console.error(`Error in WebSocket listener for ${type}:`, error);
        }
      });
    }
  }

  /**
   * Handles WebSocket reconnection
   */
  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  /**
   * Sends a message through WebSocket
   * @param {Object} message - Message to send
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
      throw new Error('WebSocket is not connected');
    }
  }

  /**
   * Adds an event listener for WebSocket messages
   * @param {string} type - Message type
   * @param {Function} callback - Callback function
   */
  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type).add(callback);
  }

  /**
   * Removes an event listener
   * @param {string} type - Message type
   * @param {Function} callback - Callback function
   */
  off(type, callback) {
    if (this.listeners.has(type)) {
      this.listeners.get(type).delete(callback);
    }
  }

  /**
   * Disconnects the WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  /**
   * Checks if WebSocket is connected
   * @returns {boolean} Connection status
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// Create singleton instances
const apiClient = new ApiClient();
const wsClient = new WebSocketClient();

export { apiClient, wsClient };
export default apiClient; 