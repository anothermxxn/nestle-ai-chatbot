/**
 * Error types for categorization
 */
export const ERROR_TYPES = {
  NETWORK: 'NETWORK',
  API: 'API',
  VALIDATION: 'VALIDATION',
  UNKNOWN: 'UNKNOWN',
};

/**
 * Categorizes an error based on its properties
 * @param {Error} error - The error to categorize
 * @returns {string} Error type
 */
export const categorizeError = (error) => {
  if (!error) return ERROR_TYPES.UNKNOWN;
  
  const message = error.message?.toLowerCase() || '';
  
  if (message.includes('fetch') || message.includes('network') || message.includes('connection')) {
    return ERROR_TYPES.NETWORK;
  }
  
  if (message.includes('http') || message.includes('api') || error.status) {
    return ERROR_TYPES.API;
  }
  
  if (message.includes('validation') || message.includes('invalid')) {
    return ERROR_TYPES.VALIDATION;
  }
  
  return ERROR_TYPES.UNKNOWN;
};

/**
 * Formats an error for user display
 * @param {Error} error - The error to format
 * @returns {Object} Formatted error object
 */
export const formatError = (error) => {
  const type = categorizeError(error);
  
  const baseError = {
    type,
    timestamp: new Date().toISOString(),
    original: error,
  };
  
  switch (type) {
    case ERROR_TYPES.NETWORK:
      return {
        ...baseError,
        title: 'Connection Error',
        message: 'Unable to connect to the server. Please check your internet connection and try again.',
        userMessage: 'Please check your connection and try again.',
        retryable: true,
      };
      
    case ERROR_TYPES.API:
      return {
        ...baseError,
        title: 'Server Error',
        message: error.message || 'The server encountered an error processing your request.',
        userMessage: 'Sorry, something went wrong. Please try again.',
        retryable: true,
      };
      
    case ERROR_TYPES.VALIDATION:
      return {
        ...baseError,
        title: 'Input Error',
        message: error.message || 'Please check your input and try again.',
        userMessage: error.message || 'Please check your input.',
        retryable: false,
      };
      
    default:
      return {
        ...baseError,
        title: 'Unexpected Error',
        message: error.message || 'An unexpected error occurred.',
        userMessage: 'Something unexpected happened. Please try again.',
        retryable: true,
      };
  }
};

/**
 * Logs an error with context information
 * @param {Error} error - The error to log
 * @param {Object} context - Additional context information
 */
export const logError = (error, context = {}) => {
  const formattedError = formatError(error);
  
  console.group(`🚨 ${formattedError.title}`);
  console.error('Error:', error);
  console.log('Type:', formattedError.type);
  console.log('Message:', formattedError.message);
  console.log('Timestamp:', formattedError.timestamp);
  
  if (Object.keys(context).length > 0) {
    console.log('Context:', context);
  }
  
  if (error.stack) {
    console.log('Stack trace:', error.stack);
  }
  
  console.groupEnd();
};

/**
 * Creates a user-friendly error handler function
 * @param {Function} setError - State setter for error display
 * @param {Object} options - Handler options
 * @returns {Function} Error handler function
 */
export const createErrorHandler = (setError, options = {}) => {
  const { 
    logErrors = true, 
    showToast = false, 
    context = {} 
  } = options;
  
  return (error) => {
    const formattedError = formatError(error);
    
    if (logErrors) {
      logError(error, context);
    }
    
    if (setError) {
      setError(formattedError.userMessage);
    }
    
    if (showToast && window.showToast) {
      window.showToast(formattedError.userMessage, 'error');
    }
    
    return formattedError;
  };
};

/**
 * Retry wrapper for functions that might fail
 * @param {Function} fn - Function to retry
 * @param {Object} options - Retry options
 * @returns {Promise} Result of the function
 */
export const withRetry = async (fn, options = {}) => {
  const { 
    maxAttempts = 3, 
    delay = 1000, 
    backoff = true,
    onRetry = null 
  } = options;
  
  let lastError;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxAttempts) {
        throw error;
      }
      
      const formattedError = formatError(error);
      if (!formattedError.retryable) {
        throw error;
      }
      
      if (onRetry) {
        onRetry(error, attempt, maxAttempts);
      }
      
      const waitTime = backoff ? delay * attempt : delay;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
  
  throw lastError;
};

export default {
  ERROR_TYPES,
  categorizeError,
  formatError,
  logError,
  createErrorHandler,
  withRetry,
}; 