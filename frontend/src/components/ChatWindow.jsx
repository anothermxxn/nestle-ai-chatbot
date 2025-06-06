import { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  TextField, 
  Alert,
  Tooltip
} from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import { Send, ExpandMore, Close, LocationOn, Refresh } from '@mui/icons-material';
import MessageBubble from './MessageBubble';
import { 
  colors, 
  fontFamily, 
  FlexBetween, 
  FlexCenter, 
  shadows, 
  StyledIconButton,
  NestleHeader,
  mediaQueries
} from './common';
import useChatSession from '../hooks/useChatSession';
import { createErrorHandler } from '../utils/errorHandler';
import { validateFSA, getFSAValidationMessage, formatFSA } from '../utils/validation';

import nestleLogoCircle from '../assets/logoCircle.jpg';

// Nestlé Logo for header avatar
const HeaderNestleLogo = styled('img')({
  width: 32,
  height: 32,
  borderRadius: '50%',
  objectFit: 'cover',
  border: `1px solid ${colors.primary}`,
  background: colors.white,
  padding: 2,
  boxShadow: '0 2px 8px rgba(99, 81, 61, 0.2)',
  [mediaQueries.mobile]: {
    width: 28,
    height: 28,
  },
});

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
  borderRadius: 12,
  boxShadow: shadows.nestle,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  fontFamily,
  fontWeight: 600,
  [mediaQueries.mobile]: {
    width: '100%',
    height: '100%',
    borderRadius: 12,
    boxShadow: shadows.mobile,
  },
});

const ChatHeader = styled(NestleHeader)({
  padding: '14px 16px',
  background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.nestleGray} 100%)`,
  position: 'relative',
  [mediaQueries.mobile]: {
    padding: '12px 14px',
  },
});

const SmartieHeader = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: 12,
  flex: 1,
  overflow: 'hidden',
  [mediaQueries.mobile]: {
    gap: 10,
    minWidth: 0,
  },
});

const SmartieTitle = styled(Typography)({
  fontWeight: 700,
  fontSize: 16,
  letterSpacing: '0.8px',
  color: colors.nestleCream,
  fontFamily,
  [mediaQueries.mobile]: {
    fontSize: 18,
    letterSpacing: '0.6px',
  },
});

const HeaderControls = styled(FlexCenter)({
  gap: 8,
  [mediaQueries.mobile]: {
    gap: 6,
  },
});

const LocationIcon = styled(LocationOn, {
  shouldForwardProp: (prop) => prop !== 'hasError'
})(({ hasError }) => ({
  fontSize: 16,
  color: hasError ? '#ff6b6b' : colors.nestleCream,
  marginLeft: 8,
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  [mediaQueries.mobile]: {
    fontSize: 16,
    marginLeft: 8,
    marginRight: 0,
  },
}));

const LocationRefreshIcon = styled(Refresh, {
  shouldForwardProp: (prop) => prop !== 'hasError'
})(({ hasError }) => ({
  fontSize: 16,
  color: hasError ? '#ff6b6b' : colors.nestleCream,
  marginLeft: 8,
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  '&:hover': {
    transform: 'rotate(90deg)',
  },
  [mediaQueries.mobile]: {
    fontSize: 16,
    marginLeft: 8,
  },
}));

const LocationContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isEditingLocation'
})(({ isEditingLocation }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  ...(isEditingLocation ? {
    // In editing mode: always show refresh icon
    '& .location-icon': {
      display: 'none',
    },
    '& .location-refresh': {
      display: 'block',
    },
  } : {
    // Outside editing mode: show location icon, refresh on hover
    '& .location-icon': {
      display: 'block',
    },
    '& .location-refresh': {
      display: 'none',
    },
    '&:hover .location-icon': {
      display: 'none',
    },
    '&:hover .location-refresh': {
      display: 'block',
    },
  }),
}));

const LocationTextInline = styled(Typography, {
  shouldForwardProp: (prop) => prop !== 'isEditing' && prop !== 'hasError'
})(({ isEditing, hasError }) => ({
  fontSize: 16,
  fontWeight: 500,
  color: hasError ? '#ff6b6b' : colors.nestleCream,
  fontFamily,
  cursor: isEditing ? 'text' : 'pointer',
  textDecoration: 'underline',
  textDecorationColor: hasError ? '#ff6b6b' : colors.nestleCream,
  textUnderlineOffset: 2,
  minWidth: 60,
  padding: '2px 4px',
  borderRadius: 4,
  background: 'transparent',
  transition: 'all 0.2s ease',
  [mediaQueries.mobile]: {
    fontSize: 18,
    minWidth: 70,
    padding: '4px 6px',
  },
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
}));

const LocationInputInline = styled('input')(({ isValid }) => ({
  fontSize: 16,
  fontWeight: 500,
  color: colors.nestleCream,
  fontFamily,
  background: colors.nestleGray,
  border: `1px solid ${isValid === false ? '#ff6b6b' : 'transparent'}`,
  outline: 'none',
  borderRadius: 4,
  padding: '2px 6px',
  minWidth: 50,
  maxWidth: 80,
  textDecoration: 'none',
  transition: 'border-color 0.2s ease',
  [mediaQueries.mobile]: {
    fontSize: 18,
    padding: '4px 8px',
    minWidth: 60,
    maxWidth: 90,
  },
}));

const MessagesContainer = styled(Box)({
  flex: 1,
  overflowY: 'auto',
  padding: 12,
  background: colors.nestleGray,
  display: 'flex',
  flexDirection: 'column',
  [mediaQueries.mobile]: {
    padding: 10,
  },
  '&::-webkit-scrollbar': {
    width: 6,
  },
  '&::-webkit-scrollbar-track': {
    background: colors.nestleGray,
    borderRadius: 3,
  },
  '&::-webkit-scrollbar-thumb': {
    background: colors.primary,
    borderRadius: 3,
    '&:hover': {
      background: colors.nestleCream,
      opacity: 0.8,
    },
  },
});

const LoadingContainer = styled(Box)({
  display: 'flex',
  justifyContent: 'flex-start',
  margin: '8px 0',
  [mediaQueries.mobile]: {
    margin: '6px 0',
  },
});

const LoadingDots = styled(Box)({
  background: colors.white,
  padding: '12px 16px',
  borderRadius: 18,
  display: 'flex',
  gap: 4,
  alignItems: 'center',
  border: `1px solid ${colors.gray200}`,
  boxShadow: shadows.light,
  [mediaQueries.mobile]: {
    padding: '10px 14px',
    borderRadius: 16,
  },
});

const LoadingDot = styled(Box)(({ delay = 0 }) => ({
  width: 6,
  height: 6,
  background: colors.nestleCream,
  borderRadius: '50%',
  animation: `${loadingBounce} 1.4s infinite ease-in-out`,
  animationDelay: `${delay}s`,
  [mediaQueries.mobile]: {
    width: 5,
    height: 5,
  },
}));

const InputArea = styled(Box)({
  padding: '12px',
  background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.nestleGray} 100%)`,
  [mediaQueries.mobile]: {
    padding: '10px',
  },
});

const InputContainer = styled(FlexCenter)({
  gap: 8,
  background: colors.nestleGray,
  border: `1px solid ${colors.nestleCream}`,
  borderRadius: 8,
  padding: '4px 6px',
  width: '100%',
  transition: 'border-color 0.2s ease',
  [mediaQueries.mobile]: {
    gap: 6,
    padding: '6px 8px',
    borderRadius: 10,
  },
  '&:focus-within': {
    borderColor: colors.primary,
  },
});

const MessageInput = styled(TextField)({
  flex: 1,
  '& .MuiOutlinedInput-root': {
    border: 'none',
    background: 'transparent',
    fontSize: 14,
    fontFamily,
    fontWeight: 500,
    [mediaQueries.mobile]: {
      fontSize: 16,
    },
    '& fieldset': {
      border: 'none',
    },
    '&:hover fieldset': {
      border: 'none',
    },
    '&.Mui-focused fieldset': {
      border: 'none',
    },
    '&.Mui-disabled fieldset': {
      border: 'none',
    },
  },
  '& .MuiOutlinedInput-input': {
    padding: '8px 12px',
    color: colors.nestleCream,
    [mediaQueries.mobile]: {
      padding: '10px 14px',
      fontSize: 16,
    },
    '&::placeholder': {
      color: colors.gray500,
      fontWeight: 500,
      opacity: 1,
    },
    '&.Mui-disabled': {
      color: colors.nestleCream,
      WebkitTextFillColor: colors.nestleCream,
      '&::placeholder': {
        color: colors.gray500,
        fontWeight: 500,
        opacity: 1,
        WebkitTextFillColor: colors.gray500,
      },
    },
  },
});

/**
 * Main chat window component that handles the main chat interface and messaging
 * @param {Function} onClose            - Callback to close the chat window
 * @param {Function} onCollapse         - Callback to collapse the chat window
 * @param {number} resetTrigger         - Trigger to reset conversation
 * @param {Object} location             - Current location data (FSA)
 * @param {Function} onLocationRefresh  - Callback to refresh location
 * @param {Function} onLocationUpdate   - Callback to update location manually
 * @param {Object} style                - Additional styles for the container
 * @returns {JSX.Element} Chat window interface
 */
const ChatWindow = ({ onClose, onCollapse, resetTrigger, location, onLocationRefresh, onLocationUpdate, style }) => {
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isEditingLocation, setIsEditingLocation] = useState(false);
  const [locationInputValue, setLocationInputValue] = useState("");

  // Conversation management
  const {
    conversationHistory,
    sendMessage,
    resetConversation
  } = useChatSession();

  // Reference for auto-scrolling
  const messagesEndRef = useRef(null);
  const latestMessageRef = useRef(null);
  const isInitialMount = useRef(true);
  const previousMessageCount = useRef(0);

  const handleError = createErrorHandler(setError, {
    context: { component: 'ChatWindow' }
  });

  // Convert conversation history to display format
  const displayMessages = useMemo(() => {
    const messages = conversationHistory.map((msg, index) => ({
      id: index + 2,
      type: msg.role,
      content: msg.content,
      references: msg.metadata?.sources || [],
      timestamp: new Date(msg.timestamp),
    }));

    // Always add welcome message as the first message
    const welcomeMessage = {
      id: 1,
      type: "assistant",
      content: "Hey! I'm Smartie, your personal MadeWithNestle assistant. Ask me anything, and I'll quickly search the entire site to find the answers you need!",
      references: [],
      timestamp: new Date(),
    };

    return [welcomeMessage, ...messages];
  }, [conversationHistory]);

  // Auto-scroll 
  useEffect(() => {
    if (displayMessages.length > 0) {
      const isNewMessage = displayMessages.length > previousMessageCount.current;
      
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
      
        previousMessageCount.current = displayMessages.length;
    }
  }, [displayMessages, isInitializing]);

  // Reset conversation when chat is closed/reopened cycle completes
  const previousResetTrigger = useRef(0);
  useEffect(() => {
    if (resetTrigger > previousResetTrigger.current && !isInitialMount.current) {
      resetConversation();
      setError(null);
    }
    previousResetTrigger.current = resetTrigger;
  }, [resetTrigger, resetConversation]);

  // Initialize component
  useEffect(() => {
    // Complete initialization after next render
    setTimeout(() => setIsInitializing(false), 0);
    isInitialMount.current = false;
  }, []);

  /**
   * Handles sending a new message to the chat API
   * Manages loading states and error handling
   */
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const messageText = inputValue;
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      await sendMessage(messageText);
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

  /**
   * Handles starting location edit mode
   */
  const handleLocationEdit = () => {
    setLocationInputValue(location?.fsa || "");
    setIsEditingLocation(true);
  };

  /**
   * Handles canceling location edit
   */
  const handleLocationCancel = () => {
    setIsEditingLocation(false);
    setLocationInputValue("");
  };

  /**
   * Handles Enter key in location input
   */
  const handleLocationKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleLocationSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleLocationCancel();
    }
  };

  /**
   * Handles saving location edit with validation
   */
  const handleLocationSave = () => {
    const trimmedInput = locationInputValue.trim().toUpperCase();
    
    if (!trimmedInput) {
      setIsEditingLocation(false);
      return;
    }
    
    if (!validateFSA(trimmedInput)) {
      return; // Keep editing mode, validation shown via tooltip
    }
    
    if (onLocationUpdate) {
      onLocationUpdate(trimmedInput);
    }
    setIsEditingLocation(false);
  };

  /**
   * Handles blur event with validation
   */
  const handleLocationBlur = () => {
    const trimmedInput = locationInputValue.trim().toUpperCase();
    
    // If empty input, close editing mode
    if (!trimmedInput) {
      setIsEditingLocation(false);
      return;
    }
    
    // If invalid input, revert to original value and close editing
    if (!validateFSA(trimmedInput)) {
      setIsEditingLocation(false);
      setLocationInputValue("");
      return;
    }
    
    // If valid input, save it
    if (onLocationUpdate) {
      onLocationUpdate(trimmedInput);
    }
    setIsEditingLocation(false);
  };

  /**
   * Handles input change with real-time validation and formatting
   */
  const handleLocationInputChange = (e) => {
    const formatted = formatFSA(e.target.value);
    setLocationInputValue(formatted);
  };

  /**
   * Handles location refresh
   */
  const handleLocationRefresh = () => {
    if (onLocationRefresh) {
      onLocationRefresh();
    }
  };

  /**
   * Renders the location indicator component
   */
  const renderLocationIndicator = () => {
    if (!location) return "Location";

    if (isEditingLocation) {
      const inputValue = locationInputValue.trim();
      const isValid = inputValue.length === 0 ? null : validateFSA(inputValue);
      const validationMessage = getFSAValidationMessage(inputValue);
      const showTooltip = validationMessage !== '';
      
      return (
        <Tooltip
          title={validationMessage}
          open={showTooltip}
          placement="top"
          arrow
          sx={{
            '& .MuiTooltip-tooltip': {
              backgroundColor: '#ff6b6b',
              color: 'white',
              fontSize: 12,
              fontWeight: 500,
              padding: '6px 12px',
              borderRadius: 6,
              maxWidth: 200,
            },
            '& .MuiTooltip-arrow': {
              color: '#ff6b6b',
            },
          }}
        >
          <LocationInputInline
            value={locationInputValue}
            onChange={handleLocationInputChange}
            onKeyDown={handleLocationKeyDown}
            onBlur={handleLocationBlur}
            placeholder="E.g. K1A"
            isValid={isValid}
            autoFocus
            maxLength={3}
          />
        </Tooltip>
      );
    }

    if (location.loading) {
      return (
        <LocationTextInline 
          isEditing={false} 
          hasError={false}
          onClick={handleLocationEdit}
        >
          Detecting...
        </LocationTextInline>
      );
    }

    if (location.error) {
      return (
        <LocationTextInline 
          isEditing={false} 
          hasError={true}
          onClick={handleLocationEdit}
          title="Location detection failed. Click to enter manually or try: System Preferences > Security & Privacy > Location Services > Enable Safari"
        >
          Location
        </LocationTextInline>
      );
    }

    return (
      <LocationTextInline 
        isEditing={false} 
        hasError={false}
        onClick={handleLocationEdit}
        onDoubleClick={handleLocationRefresh}
      >
        {location.fsa || "Location"}
      </LocationTextInline>
    );
  };

  return (
    <ChatWindowContainer elevation={8} style={style}>
      {/* Chat Header */}
      <ChatHeader>
        <FlexBetween sx={{ width: '100%' }}>
          <SmartieHeader>
            <HeaderNestleLogo 
              src={nestleLogoCircle} 
              alt="Nestlé Logo"
              loading="lazy"
            />
            <SmartieTitle variant="h6">SMARTIE</SmartieTitle>
            
            {/* Inline Location Indicator */}
            <LocationContainer isEditingLocation={isEditingLocation}>
              <LocationIcon hasError={location?.error} className="location-icon" />
              <LocationRefreshIcon hasError={location?.error} className="location-refresh" onClick={handleLocationRefresh} />
              {renderLocationIndicator()}
            </LocationContainer>
          </SmartieHeader>
          
          <HeaderControls>
            <StyledIconButton variant="header" onClick={onCollapse} size="small">
              <ExpandMore sx={{ fontSize: 18 }} />
            </StyledIconButton>
            <StyledIconButton variant="header" onClick={onClose} size="small">
              <Close sx={{ fontSize: 18 }} />
            </StyledIconButton>
          </HeaderControls>
        </FlexBetween>
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
            {displayMessages.map((message, index) => (
              <MessageBubble 
                key={message.id} 
                message={message}
                ref={index === displayMessages.length - 1 ? latestMessageRef : null}
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
            <Send sx={{ fontSize: 16 }} />
          </StyledIconButton>
        </InputContainer>
      </InputArea>
    </ChatWindowContainer>
  );
};

export default ChatWindow; 