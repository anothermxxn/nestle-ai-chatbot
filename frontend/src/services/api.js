/**
 * API client for communicating with the Nestle AI Chatbot backend
 * Handles HTTP requests and WebSocket connections
 */

import { API_CONFIG } from '../config/api';

const API_BASE_URL = API_CONFIG.baseURL;

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
}

// Create singleton instance
const apiClient = new ApiClient();

export default apiClient; 