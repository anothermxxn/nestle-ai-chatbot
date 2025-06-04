import { useState, useEffect, useCallback } from 'react';
import apiClient from '../services/api';

/**
 * Custom hook for managing chat sessions with context memory
 * Sessions are removed when the page is refreshed or closed
 * @returns {Object} Session management state and methods
 */
const useChatSession = () => {
  const [sessionId, setSessionId] = useState(null);
  const [isSessionLoading, setIsSessionLoading] = useState(false);
  const [sessionError, setSessionError] = useState(null);

  /**
   * Helper to clear session storage
   */
  const clearSessionStorage = useCallback(() => {
    sessionStorage.removeItem('chatSessionId');
  }, []);

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
      sessionStorage.setItem('chatSessionId', newSessionId);
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
   * Deletes the current session
   */
  const deleteSession = useCallback(async () => {
    if (!sessionId) return;
    
    setIsSessionLoading(true);
    setSessionError(null);
    
    try {
      await apiClient.deleteSession(sessionId);
      setSessionId(null);
      clearSessionStorage();
    } catch (error) {
      console.error('Failed to delete session:', error);
      setSessionError(error.message);
    } finally {
      setIsSessionLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

  /**
   * Cleanup session before page unload
   */
  const cleanupSession = useCallback(async () => {
    if (sessionId) {
      try {
        if (navigator.sendBeacon) {
          const url = `${apiClient.baseURL}/chat/session/${sessionId}/delete`;
          const success = navigator.sendBeacon(url, JSON.stringify({}));
          if (!success) {
            console.warn("sendBeacon failed, session may not be cleaned up");
          }
        } else {
          await apiClient.deleteSession(sessionId);
        }
      } catch (error) {
        console.error("Failed to cleanup session on page unload:", error);
      }
    }
  }, [sessionId]);

  // Initialize session on mount
  useEffect(() => {
    const initializeSession = async () => {
      const existingSessionId = sessionStorage.getItem('chatSessionId');
      
      if (existingSessionId) {
        try {
          const history = await apiClient.getSessionHistory(existingSessionId);
          if (history) {
            setSessionId(existingSessionId);
            return;
          }
        } catch (error) {
          console.warn('Failed to restore existing session, creating new one:', error);
        }
        clearSessionStorage();
      }
      
      await createSession();
    };

    initializeSession();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [createSession]);

  // Cleanup on page unload
  useEffect(() => {
    const handleBeforeUnload = () => {
      cleanupSession();
      clearSessionStorage();
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cleanupSession]);

  return {
    sessionId,
    isSessionLoading,
    sessionError,
    createSession,
    deleteSession,
    getSessionHistory,
    sendMessage,
    hasActiveSession: !!sessionId,
    resetSession
  };
};

export default useChatSession; 