/**
 * API client for communicating with the Nestle AI Chatbot backend
 * Handles HTTP requests and session management
 */

import { API_CONFIG } from '../config/api';

const API_BASE_URL = API_CONFIG.baseURL;

/**
 * HTTP API client class for REST endpoints with session management
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