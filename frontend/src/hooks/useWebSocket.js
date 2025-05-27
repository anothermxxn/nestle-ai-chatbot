import { useState, useEffect, useRef, useCallback } from 'react';
import { wsClient } from '../services/api';

/**
 * Custom hook for managing WebSocket connections
 * @param {string} conversationId - Optional conversation ID for grouped chats
 * @param {Object} options - Configuration options
 * @returns {Object} WebSocket state and methods
 */
const useWebSocket = (conversationId = null, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  
  const {
    autoConnect = false,
    onMessage = null,
    onError = null,
    onConnect = null,
    onDisconnect = null,
  } = options;

  const messageHandlersRef = useRef(new Map());

  /**
   * Connects to the WebSocket server
   */
  const connect = useCallback(async () => {
    try {
      setConnectionError(null);
      await wsClient.connect(conversationId);
      setIsConnected(true);
      onConnect?.();
    } catch (error) {
      setConnectionError(error.message);
      setIsConnected(false);
      onError?.(error);
    }
  }, [conversationId, onConnect, onError]);

  /**
   * Disconnects from the WebSocket server
   */
  const disconnect = useCallback(() => {
    wsClient.disconnect();
    setIsConnected(false);
    setMessages([]);
    setIsTyping(false);
    onDisconnect?.();
  }, [onDisconnect]);

  /**
   * Sends a message through WebSocket
   * @param {Object} message - Message to send
   */
  const sendMessage = useCallback((message) => {
    if (isConnected) {
      wsClient.send(message);
    } else {
      throw new Error('WebSocket is not connected');
    }
  }, [isConnected]);

  /**
   * Sends a chat message
   * @param {string} text - Message text
   */
  const sendChatMessage = useCallback((text) => {
    sendMessage({
      type: 'chat',
      message: text,
      timestamp: Date.now(),
    });
  }, [sendMessage]);

  /**
   * Sends typing indicator
   * @param {boolean} typing - Whether user is typing
   */
  const sendTypingIndicator = useCallback((typing) => {
    sendMessage({
      type: 'typing',
      is_typing: typing,
    });
  }, [sendMessage]);

  /**
   * Sends ping for connection health check
   */
  const sendPing = useCallback(() => {
    sendMessage({
      type: 'ping',
      timestamp: Date.now(),
    });
  }, [sendMessage]);

  // Set up message handlers
  useEffect(() => {
    const handleChatResponse = (data) => {
      const newMessage = {
        id: Date.now(),
        type: 'assistant',
        content: data.message,
        references: data.references || [],
        timestamp: new Date(data.timestamp * 1000),
      };
      setMessages(prev => [...prev, newMessage]);
      onMessage?.(newMessage);
    };

    const handleTyping = (data) => {
      if (data.sender === 'assistant') {
        setIsTyping(data.is_typing);
      }
    };

    const handleError = (data) => {
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        content: data.message,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      onError?.(new Error(data.message));
    };

    const handleSystem = (data) => {
      console.log('WebSocket system message:', data.message);
    };

    const handlePong = (data) => {
      console.log('WebSocket pong received:', data.timestamp);
    };

    // Register handlers
    wsClient.on('chat_response', handleChatResponse);
    wsClient.on('typing', handleTyping);
    wsClient.on('error', handleError);
    wsClient.on('system', handleSystem);
    wsClient.on('pong', handlePong);

    // Store handlers for cleanup
    messageHandlersRef.current.set('chat_response', handleChatResponse);
    messageHandlersRef.current.set('typing', handleTyping);
    messageHandlersRef.current.set('error', handleError);
    messageHandlersRef.current.set('system', handleSystem);
    messageHandlersRef.current.set('pong', handlePong);

    return () => {
      // Cleanup handlers
      messageHandlersRef.current.forEach((handler, type) => {
        wsClient.off(type, handler);
      });
      messageHandlersRef.current.clear();
    };
  }, [onMessage, onError]);

  // Auto-connect if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, connect, disconnect]);

  // Update connection status based on wsClient state
  useEffect(() => {
    const checkConnection = () => {
      setIsConnected(wsClient.isConnected());
    };

    const interval = setInterval(checkConnection, 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    // Connection state
    isConnected,
    connectionError,
    
    // Messages and typing
    messages,
    isTyping,
    
    // Connection methods
    connect,
    disconnect,
    
    // Messaging methods
    sendMessage,
    sendChatMessage,
    sendTypingIndicator,
    sendPing,
    
    // Utility methods
    clearMessages: () => setMessages([]),
    addMessage: (message) => setMessages(prev => [...prev, message]),
  };
};

export default useWebSocket; 