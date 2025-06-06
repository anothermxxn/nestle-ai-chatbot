import { useState, useEffect, useCallback } from 'react';
import apiClient from './api';

/**
 * Custom hook for managing chat conversation sessions with backend session management
 * @returns {Object} Chat session management state and methods
 */
const useChatSession = () => {
  const [sessionId, setSessionId] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Storage key for session ID persistence
   */
  const SESSION_ID_STORAGE_KEY = 'nestleChatSessionId';
  const RELOAD_FLAG_KEY = 'nestleChatReloadFlag';

  /**
   * Helper to detect if this is a page reload
   */
  const isPageReload = useCallback(() => {
    const reloadFlag = sessionStorage.getItem(RELOAD_FLAG_KEY);
    return reloadFlag === 'true';
  }, []);

  /**
   * Helper to set reload detection flag
   */
  const setReloadFlag = useCallback(() => {
    sessionStorage.setItem(RELOAD_FLAG_KEY, 'true');
  }, []);

  /**
   * Helper to clear reload detection flag
   */
  const clearReloadFlag = useCallback(() => {
    sessionStorage.removeItem(RELOAD_FLAG_KEY);
  }, []);

  /**
   * Load session ID from storage
   */
  const loadSessionId = useCallback(() => {
    try {
      // If this is a page reload, clear the session and start fresh
      if (isPageReload()) {
        sessionStorage.removeItem(SESSION_ID_STORAGE_KEY);
        clearReloadFlag();
        return null;
      }

      const stored = sessionStorage.getItem(SESSION_ID_STORAGE_KEY);
      if (stored) {
        setSessionId(stored);
        return stored;
      }
    } catch (error) {
      console.warn('Failed to load session ID from storage:', error);
    }
    return null;
  }, [isPageReload, clearReloadFlag]);

  /**
   * Save session ID to storage
   */
  const saveSessionId = useCallback((id) => {
    try {
      if (id) {
        sessionStorage.setItem(SESSION_ID_STORAGE_KEY, id);
      } else {
        sessionStorage.removeItem(SESSION_ID_STORAGE_KEY);
      }
    } catch (error) {
      console.warn('Failed to save session ID to storage:', error);
    }
  }, []);

  /**
   * Create a new session
   */
  const createSession = useCallback(async () => {
    try {
      const response = await apiClient.createSession();
      const newSessionId = response.session_id;
      
      setSessionId(newSessionId);
      saveSessionId(newSessionId);
      
      return newSessionId;
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error.message);
      throw error;
    }
  }, [saveSessionId]);

  /**
   * Load conversation history for current session
   */
  const loadConversationHistory = useCallback(async (sessionIdToLoad) => {
    if (!sessionIdToLoad) return [];

    try {
      const response = await apiClient.getConversationHistory(sessionIdToLoad);
      const history = response.messages || [];
      setConversationHistory(history);
      return history;
    } catch (error) {
      console.warn('Failed to load conversation history:', error);
      // If session not found, clear it and start fresh
      if (error.message.includes('404') || error.message.includes('not found')) {
        setSessionId(null);
        saveSessionId(null);
        setConversationHistory([]);
      }
      return [];
    }
  }, [saveSessionId]);

  /**
   * Sends a chat message using session management
   */
  const sendMessage = useCallback(async (message, location = null) => {
    setIsLoading(true);
    setError(null);
    
    try {
      let currentSessionId = sessionId;
      
      // Create session if none exists
      if (!currentSessionId) {
        currentSessionId = await createSession();
      }
      
      const userMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      
      setConversationHistory(prev => [...prev, userMessage]);
      
      // Prepare location data for backend
      let userLocationData = null;
      if (location && location.coords && location.coords.latitude && location.coords.longitude) {
        userLocationData = {
          lat: location.coords.latitude,
          lon: location.coords.longitude
        };
      }
      
      const response = await apiClient.sendChatMessage(message, currentSessionId, {}, userLocationData);
      
      // Update session ID if it was created by the backend
      if (response.session_id && response.session_id !== currentSessionId) {
        setSessionId(response.session_id);
        saveSessionId(response.session_id);
        currentSessionId = response.session_id;
      }
      
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        metadata: {
          sources: response.sources,
          search_results_count: response.search_results_count,
          filters_applied: response.filters_applied,
          graphrag_enhanced: response.graphrag_enhanced,
          is_purchase_query: response.is_purchase_query,
          purchase_assistance: response.purchase_assistance
        }
      };

      if (response.purchase_assistance) {
        assistantMessage.purchase_assistance = response.purchase_assistance;
      }
      
      setConversationHistory(prev => [...prev, assistantMessage]);
      
      return response;
    } catch (error) {
      console.error('Failed to send message:', error);
      setError(error.message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, createSession, saveSessionId]);

  /**
   * Reset conversation session
   */
  const resetConversation = useCallback(async () => {
    try {
      // Delete current session if it exists
      if (sessionId) {
        await apiClient.deleteSession(sessionId);
      }
    } catch (error) {
      console.warn('Failed to delete session:', error);
    } finally {
      // Clear local state regardless
      setSessionId(null);
      setConversationHistory([]);
      saveSessionId(null);
    }
  }, [sessionId, saveSessionId]);

  /**
   * Initialize session on mount
   */
  useEffect(() => {
    const initializeSession = async () => {
      // Set the reload flag so we can detect if the user refreshes the page
      setReloadFlag();
      
      // Load session ID (will be null if this is a reload)
      const storedSessionId = loadSessionId();
      
      if (storedSessionId) {
        // Load conversation history for existing session
        await loadConversationHistory(storedSessionId);
      }
    };

    initializeSession();
  }, [loadSessionId, loadConversationHistory, setReloadFlag]);

  /**
   * Set up beforeunload handler to clear reload flag
   */
  useEffect(() => {
    const handleBeforeUnload = () => {
      clearReloadFlag();
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [clearReloadFlag]);

  return {
    sessionId,
    conversationHistory,
    isLoading,
    error,
    sendMessage,
    resetConversation
  };
};

export { useChatSession }; 