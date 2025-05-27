import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import ChatWindow from './ChatWindow';
import { colors, fontFamily, FlexCenter, shadows, StyledAvatar } from './common';
import useChatSession from '../hooks/useChatSession';

// Animation keyframes for chat window transitions
const expandToWindow = keyframes`
  from {
    width: 70px;
    height: 70px;
    border-radius: 50%;
  }
  to {
    width: 400px;
    height: 600px;
    border-radius: 8px;
  }
`;

const collapseToRectangle = keyframes`
  from {
    width: 400px;
    height: 600px;
    border-radius: 8px;
  }
  to {
    width: 400px;
    height: 50px;
    border-radius: 8px;
  }
`;

const expandFromRectangle = keyframes`
  from {
    width: 400px;
    height: 50px;
    border-radius: 8px;
  }
  to {
    width: 400px;
    height: 600px;
    border-radius: 8px;
  }
`;

const collapseToCircle = keyframes`
  from {
    width: 400px;
    height: 600px;
    border-radius: 8px;
  }
  to {
    width: 70px;
    height: 70px;
    border-radius: 50%;
  }
`;

const fadeInContent = keyframes`
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

// Styled components
const ChatContainer = styled(Box)({
  position: 'fixed',
  zIndex: 1000,
  fontFamily,
  fontWeight: 600,
});

/**
 * Animated container that handles all chat window state transitions
 */
const AnimatedContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'chatState',
})(({ chatState }) => {
  const baseStyles = {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    background: colors.primary,
    border: `1px solid ${colors.white}`,
    boxShadow: shadows.medium,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
  };

  switch (chatState) {
    case 'circle':
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        cursor: 'pointer',
        '&:hover': {
          transform: 'scale(1.05)',
          boxShadow: '0 6px 25px rgba(0, 0, 0, 0.2)',
        },
      };
    
    case 'expanding':
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        animation: `${expandToWindow} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
      };
    
    case 'open':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '8px',
      };
    
    case 'collapsing':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '8px',
        animation: `${collapseToRectangle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
      };
    
    case 'collapsed':
      return {
        ...baseStyles,
        width: '400px',
        height: '50px',
        borderRadius: '8px',
        cursor: 'pointer',
      };
    
    case 'expanding-from-rectangle':
      return {
        ...baseStyles,
        width: '400px',
        height: '50px',
        borderRadius: '8px',
        animation: `${expandFromRectangle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
      };
    
    case 'closing':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '8px',
        animation: `${collapseToCircle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
      };
    
    default:
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
      };
  }
});

const CircleContent = styled(FlexCenter)({
  color: colors.white,
  width: '100%',
  height: '100%',
  flexDirection: 'column',
});

const SmartieText = styled(Typography)(({ size = 'normal' }) => ({
  fontSize: size === 'small' ? 12 : 9,
  fontWeight: 'bold',
  letterSpacing: '0.5px',
  textAlign: 'center',
  color: colors.white,
}));

const CollapsedContent = styled(FlexCenter)({
  gap: 12,
  color: colors.white,
  width: '100%',
  height: '100%',
  animation: `${fadeInContent} 0.2s ease 0.1s both`,
});

const ChatWindowContent = styled(Box)({
  width: '100%',
  height: '100%',
  opacity: 1,
});

/**
 * Main ChatBot component that manages the chat interface states and animations
 * Handles transitions between circle, collapsed, and expanded states
 * @returns {JSX.Element} The chatbot interface with state management
 */
const ChatBot = () => {
  const [state, setState] = useState('circle');
  const [resetTrigger, setResetTrigger] = useState(0);
  const { resetSession } = useChatSession();

  /**
   * Handles click events on the chat button/collapsed window
   * Triggers appropriate expansion animation based on current state
   */
  const handleClick = () => {
    if (state === 'circle') {
      setState('expanding');
      setTimeout(() => setState('open'), 400);
    } else if (state === 'collapsed') {
      setState('expanding-from-rectangle');
      setTimeout(() => setState('open'), 400);
    }
  };

  /**
   * Collapses the chat window to a rectangle button
   */
  const handleCollapse = () => {
    setState('collapsing');
    setTimeout(() => setState('collapsed'), 400);
  };

  /**
   * Completely closes the chat window back to the floating button
   * Also resets the chat session when closing
   */
  const handleClose = async () => {
    setState('closing');
    setTimeout(() => setState('circle'), 400);
    
    // Reset the session when closing the chat window
    try {
      await resetSession();
      // Increment reset trigger to signal ChatWindow to reset
      setResetTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Failed to reset session on close:', error);
    }
  };

  /**
   * Renders appropriate content based on current chat window state
   * @returns {JSX.Element} Content for the current state
   */
  const renderContent = () => {
    if (state === 'open') {
      return (
        <ChatWindowContent>
          <ChatWindow 
            onClose={handleClose} 
            onCollapse={handleCollapse}
            resetTrigger={resetTrigger}
          />
        </ChatWindowContent>
      );
    } else if (state === 'collapsed') {
      return (
        <CollapsedContent>
          <StyledAvatar size="small">
            <SmartToyOutlinedIcon />
          </StyledAvatar>
          <SmartieText size="small">SMARTIE - CLICK TO EXPAND</SmartieText>
        </CollapsedContent>
      );
    } else {
      return (
        <CircleContent>
          <SmartToyOutlinedIcon fontSize="large" />
        </CircleContent>
      );
    }
  };

  return (
    <ChatContainer>
      <AnimatedContainer 
        chatState={state}
        onClick={handleClick}
      >
        {renderContent()}
      </AnimatedContainer>
    </ChatContainer>
  );
};

export default ChatBot; 