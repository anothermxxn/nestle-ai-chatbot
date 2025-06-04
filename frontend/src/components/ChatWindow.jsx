import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Alert
} from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import { Send, ExpandMore, Close } from '@mui/icons-material';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import MessageBubble from './MessageBubble';
import { 
  colors, 
  fontFamily, 
  FlexBetween, 
  FlexCenter, 
  shadows, 
  StyledAvatar, 
  StyledIconButton 
} from './common';
import useChatSession from '../hooks/useChatSession';
import { createErrorHandler } from '../utils/errorHandler';

// Loading animation for typing indicator
const loadingBounce = keyframes`
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
`;

// Styled components
const ChatWindowContainer = styled(Paper)({
  width: 400,
  height: 600,
  borderRadius: 8,
  boxShadow: shadows.heavy,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  border: `1px solid ${colors.gray200}`,
  fontFamily,
  fontWeight: 600,
});

const ChatHeader = styled(FlexBetween)({
  background: colors.primary,
  color: colors.white,
  padding: '12px 16px',
});

const SmartieHeader = styled(FlexCenter)({
  gap: 12,
});

const SmartieTitle = styled(Typography)({
  fontWeight: 'bold',
  fontSize: 16,
  letterSpacing: '0.5px',
  color: colors.white,
});

const HeaderControls = styled(FlexCenter)({
  gap: 8,
});

const MessagesContainer = styled(Box)({
  flex: 1,
  overflowY: 'auto',
  padding: 16,
  background: colors.gray50,
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
  '&::-webkit-scrollbar': {
    width: 6,
  },
  '&::-webkit-scrollbar-track': {
    background: colors.gray100,
  },
  '&::-webkit-scrollbar-thumb': {
    background: colors.gray300,
    borderRadius: 3,
  },
});

const LoadingContainer = styled(Box)({
  display: 'flex',
  justifyContent: 'flex-start',
  margin: '8px 0',
});

const LoadingDots = styled(Box)({
  background: colors.gray200,
  padding: '12px 16px',
  borderRadius: 18,
  display: 'flex',
  gap: 4,
  alignItems: 'center',
});

const LoadingDot = styled(Box)(({ delay = 0 }) => ({
  width: 6,
  height: 6,
  background: colors.gray500,
  borderRadius: '50%',
  animation: `${loadingBounce} 1.4s infinite ease-in-out`,
  animationDelay: `${delay}s`,
}));

const InputArea = styled(Box)({
  padding: '10px',
  background: colors.white,
  borderTop: `1px solid ${colors.gray200}`,
});

const InputContainer = styled(FlexCenter)({
  gap: 6,
  background: colors.gray50,
  border: `1px solid ${colors.gray200}`,
  borderRadius: 6,
  padding: '2px 4px',
  width: '100%',
});

const MessageInput = styled(TextField)({
  flex: 1,
  '& .MuiOutlinedInput-root': {
    border: 'none',
    background: 'transparent',
    fontSize: 14,
    fontFamily,
    fontWeight: 500,
    '& fieldset': {
      border: 'none',
    },
    '&:hover fieldset': {
      border: 'none',
    },
    '&.Mui-focused fieldset': {
      border: 'none',
    },
  },
  '& .MuiOutlinedInput-input': {
    padding: '6px 12px',
    color: colors.gray500,
    '&::placeholder': {
      color: colors.gray400,
      fontWeight: 500,
      opacity: 1,
    },
  },
});

/**
 * Main chat window component that handles message display and user input
 * @param {Function} onClose      - Callback function to close the chat window
 * @param {Function} onCollapse   - Callback function to collapse the chat window
 * @param {number}   resetTrigger - Counter that triggers message reset when changed
 * @returns {JSX.Element} The complete chat interface
 */
const ChatWindow = ({ onClose, onCollapse, resetTrigger }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Session management
  const {
    sendMessage,
    hasActiveSession,
    getSessionHistory
  } = useChatSession();

  // Reference for auto-scrolling
  const messagesEndRef = useRef(null);
  const latestMessageRef = useRef(null);
  const isInitialMount = useRef(true);
  const previousMessageCount = useRef(0);

  const handleError = createErrorHandler(setError, {
    context: { component: 'ChatWindow' }
  });

  const createWelcomeMessage = (id = 1, timestamp = new Date()) => ({
    id,
    type: "assistant",
    content: "Hey! I'm Smartie, your personal MadeWithNestle assistant. Ask me anything, and I'll quickly search the entire site to find the answers you need!",
    timestamp,
  });

  // Auto-scroll 
  useEffect(() => {
    if (messages.length > 0) {
      const isNewMessage = messages.length > previousMessageCount.current;
      
      if (isInitializing || isInitialMount.current) {
        // Instant scroll for initial load and expand from collapsed
        messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
        if (!isInitializing) {
          isInitialMount.current = false;
        }
      } else if (isNewMessage && !isInitializing) {
        // Scroll to beginning of latest message for new messages
        if (latestMessageRef.current) {
          latestMessageRef.current.scrollIntoView({ 
            behavior: "smooth",
            block: "start",
            inline: "nearest"
          });
        } else {
          // Fallback to end scroll if ref not available
          messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
      }
      
      previousMessageCount.current = messages.length;
    }
  }, [messages, isInitializing]);

  // Reset messages when chat is actually closed
  useEffect(() => {
    if (resetTrigger > 0 && !isInitialMount.current) {
      setMessages([createWelcomeMessage()]);
      setError(null);
    }
  }, [resetTrigger]);

  // Load session history on mount
  useEffect(() => {
    const loadSessionHistory = async () => {
      if (!hasActiveSession || !isInitialMount.current) {
        setIsInitializing(false);
        return;
      }

      try {
        const history = await getSessionHistory();
        
        if (history?.messages?.length > 0) {
          const formattedMessages = history.messages.map((msg, index) => ({
            id: index + 1,
            type: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content,
            references: msg.metadata?.sources || [],
            timestamp: new Date(msg.timestamp || Date.now()),
          }));
          
          // Add welcome message if needed
          const hasWelcome = formattedMessages.some(msg => 
            msg.type === 'assistant' && msg.content.includes("Hey! I'm Smartie")
          );
          
          if (hasWelcome) {
            setMessages(formattedMessages);
          } else {
            const welcomeMessage = createWelcomeMessage(0, new Date(history.created_at || Date.now()));
            setMessages([welcomeMessage, ...formattedMessages.map(msg => ({ ...msg, id: msg.id + 1 }))]);
          }
        } else {
          // No history, show welcome message
          setMessages([createWelcomeMessage()]);
        }
      } catch (error) {
        console.error('Failed to load session history:', error);
        setMessages([createWelcomeMessage()]);
      } finally {
        // Complete initialization after next render
        setTimeout(() => setIsInitializing(false), 0);
      }
    };

    loadSessionHistory();
  }, [hasActiveSession, getSessionHistory]);

  /**
   * Handles sending a new message to the chat API
   * Manages loading states and error handling
   */
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !hasActiveSession) return;

    const messageText = inputValue;

    // Create user message
    const userMessage = {
      id: Date.now(),
      type: "user",
      content: messageText,
      timestamp: new Date(),
    };

    // Update UI with user message
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const data = await sendMessage(messageText);

      // Create assistant response message
      const assistantMessage = {
        id: Date.now() + 1,
        type: "assistant",
        content: data.answer,
        references: data.sources || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles Enter key press for sending messages if not holding Shift
   * @param {KeyboardEvent} e - The keyboard event
   */
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <ChatWindowContainer elevation={8}>
      {/* Chat Header */}
      <ChatHeader>
        <SmartieHeader>
          <StyledAvatar size="medium">
            <SmartToyOutlinedIcon />
          </StyledAvatar>
          <SmartieTitle variant="h6">SMARTIE</SmartieTitle>
        </SmartieHeader>
        <HeaderControls>
          <StyledIconButton variant="header" onClick={onCollapse} size="small">
            <ExpandMore sx={{ fontSize: 16 }} />
          </StyledIconButton>
          <StyledIconButton variant="header" onClick={onClose} size="small">
            <Close sx={{ fontSize: 16 }} />
          </StyledIconButton>
        </HeaderControls>
      </ChatHeader>

      {/* Messages Display Area */}
      <MessagesContainer>
        {isInitializing ? (
          <LoadingContainer>
            <LoadingDots>
              <LoadingDot />
              <LoadingDot delay={-0.32} />
              <LoadingDot delay={-0.16} />
            </LoadingDots>
          </LoadingContainer>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble 
                key={message.id} 
                message={message}
                ref={index === messages.length - 1 ? latestMessageRef : null}
              />
            ))}

            {/* Loading indicator when waiting for response */}
            {isLoading && (
              <LoadingContainer>
                <LoadingDots>
                  <LoadingDot />
                  <LoadingDot delay={-0.32} />
                  <LoadingDot delay={-0.16} />
                </LoadingDots>
              </LoadingContainer>
            )}

            {/* Error display */}
            {error && (
              <Alert severity="error" sx={{ margin: "8px 0", fontSize: 14 }}>
                {error}
              </Alert>
            )}

            {/* Invisible element for auto-scrolling */}
            <Box ref={messagesEndRef} />
          </>
        )}
      </MessagesContainer>

      {/* Message Input Area */}
      <InputArea>
        <InputContainer>
          <MessageInput
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything"
            disabled={isLoading}
            variant="outlined"
            size="small"
            fullWidth
          />
          <StyledIconButton
            variant="send"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            size="small"
          >
            <Send sx={{ fontSize: 14 }} />
          </StyledIconButton>
        </InputContainer>
      </InputArea>
    </ChatWindowContainer>
  );
};

export default ChatWindow; 