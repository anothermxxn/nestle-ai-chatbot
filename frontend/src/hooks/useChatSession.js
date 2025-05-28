import { useState, useEffect, useCallback } from 'react';
import apiClient from '../services/api';

/**
 * Custom hook for managing chat sessions with context memory
 * @returns {Object} Session management state and methods
 */
const useChatSession = () => {
  const [sessionId, setSessionId] = useState(null);
  const [isSessionLoading, setIsSessionLoading] = useState(false);
  const [sessionError, setSessionError] = useState(null);

  /**
   * Creates a new chat session
   */
  const createSession = useCallback(async () => {
    setIsSessionLoading(true);
    setSessionError(null);
    
    try {
      const response = await apiClient.createSession();
      const newSessionId = response.session_id;
      setSessionId(newSessionId);
      
      // Store session ID in sessionStorage for persistence
      sessionStorage.setItem('chat_session_id', newSessionId);
      
      return newSessionId;
    } catch (error) {
      console.error('Failed to create session:', error);
      setSessionError(error.message);
      return null;
    } finally {
      setIsSessionLoading(false);
    }
  }, []);

  /**
   * Loads an existing session from sessionStorage or creates a new one
   */
  const initializeSession = useCallback(async () => {
    setIsSessionLoading(true);
    setSessionError(null);
    
    try {
      const storedSessionId = sessionStorage.getItem('chat_session_id');
      
      if (storedSessionId) {
        try {
          // Verify the session still exists on the backend
          await apiClient.getSessionHistory(storedSessionId);
          setSessionId(storedSessionId);
          return storedSessionId;
        } catch (error) {
          // Session doesn't exist or expired, create a new one
          console.log('Stored session expired or invalid, creating new session. Error:', error.message);
          sessionStorage.removeItem('chat_session_id');
        }
      }
      return await createSession();
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setSessionError(error.message);
      return null;
    } finally {
      setIsSessionLoading(false);
    }
  }, [createSession]);

  /**
   * Deletes the current session
   */
  const deleteSession = useCallback(async () => {
    if (!sessionId) return;
    
    setIsSessionLoading(true);
    setSessionError(null);
    
    try {
      await apiClient.deleteSession(sessionId);
      setSessionId(null);
      sessionStorage.removeItem('chat_session_id');
    } catch (error) {
      console.error('Failed to delete session:', error);
      setSessionError(error.message);
    } finally {
      setIsSessionLoading(false);
    }
  }, [sessionId]);

  /**
   * Resets the session (deletes current and creates new)
   */
  const resetSession = useCallback(async () => {
    if (sessionId) {
      await deleteSession();
    }
    return await createSession();
  }, [sessionId, deleteSession, createSession]);

  /**
   * Gets session history
   */
  const getSessionHistory = useCallback(async () => {
    if (!sessionId) return null;
    
    try {
      return await apiClient.getSessionHistory(sessionId);
    } catch (error) {
      console.error('Failed to get session history:', error);
      setSessionError(error.message);
      return null;
    }
  }, [sessionId]);

  /**
   * Sends a chat message with session context
   */
  const sendMessage = useCallback(async (message) => {
    if (!sessionId) {
      throw new Error('No active session. Please initialize a session first.');
    }
    
    try {
      return await apiClient.sendChatMessage(message, sessionId);
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }, [sessionId]);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  return {
    sessionId,
    isSessionLoading,
    sessionError,
    createSession,
    initializeSession,
    deleteSession,
    resetSession,
    getSessionHistory,
    sendMessage,
    hasActiveSession: !!sessionId
  };
};

export default useChatSession; 