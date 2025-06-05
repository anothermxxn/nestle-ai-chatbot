import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import ChatWindow from './ChatWindow';
import { colors, fontFamily, FlexCenter, shadows, mediaQueries } from './common';
import useChatSession from '../hooks/useChatSession';

import nestleLogo from '../assets/logo.jpg';
import nestleLogoCircle from '../assets/logoCircle.jpg';

// Nestlé Logo for floating button
const FloatingNestleLogo = styled('img')({
  width: '100%',
  height: '100%',
  borderRadius: '50%',
  objectFit: 'cover',
  border: `2px solid ${colors.primary}`,
});

// Nestlé Logo for collapsed state
const CollapsedNestleLogo = styled('img')({
  width: 32,
  height: 32,
  borderRadius: '50%',
  objectFit: 'cover',
  border: `1px solid ${colors.primary}`,
  background: colors.white,
  padding: 2,
  boxShadow: '0 2px 8px rgba(99, 81, 61, 0.3)',
  [mediaQueries.mobile]: {
    width: 28,
    height: 28,
  },
});

// Nestlé Logo for closing animation
const ClosingNestleLogo = styled('img')({
  width: 60,
  height: 60,
  borderRadius: '50%',
  objectFit: 'cover',
  border: `2px solid ${colors.primary}`,
  background: colors.white,
  boxShadow: '0 2px 8px rgba(99, 81, 61, 0.3)',
  [mediaQueries.mobile]: {
    width: 50,
    height: 50,
  },
});

// Nestlé Logo for loading/expanding animation
const ExpandingNestleLogo = styled('img')({
  width: 120,
  height: 120,
  borderRadius: '50%',
  objectFit: 'cover',
  border: `3px solid ${colors.primary}`,
  background: colors.white,
  padding: 8,
  boxShadow: '0 8px 32px rgba(99, 81, 61, 0.3)',
  animation: 'pulse 1.5s ease-in-out infinite',
  [mediaQueries.mobile]: {
    width: 80,
    height: 80,
    padding: 6,
  },
  '@keyframes pulse': {
    '0%': {
      transform: 'scale(1)',
      opacity: 1,
    },
    '50%': {
      transform: 'scale(1.05)',
      opacity: 0.8,
    },
    '100%': {
      transform: 'scale(1)',
      opacity: 1,
    },
  },
});

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
    border-radius: 12px;
  }
`;

const expandToWindowMobile = keyframes`
  from {
    width: 60px;
    height: 60px;
    border-radius: 50%;
  }
  to {
    width: calc(100vw - 20px);
    height: calc(100vh - 40px);
    border-radius: 12px;
  }
`;

const collapseToRectangle = keyframes`
  from {
    width: 400px;
    height: 600px;
    border-radius: 12px;
    right: 20px;
    left: auto;
    transform: none;
  }
  to {
    width: 400px;
    height: 50px;
    border-radius: 12px;
    right: 20px;
    left: auto;
    transform: none;
  }
`;

const collapseToRectangleMobile = keyframes`
  from {
    width: calc(100vw - 20px);
    height: calc(100vh - 40px);
    border-radius: 12px;
    left: 10px;
    right: 10px;
    transform: none;
  }
  to {
    width: calc(100vw - 20px);
    height: 50px;
    border-radius: 12px;
    left: 10px;
    right: 10px;
    transform: none;
  }
`;

const expandFromRectangle = keyframes`
  from {
    width: 400px;
    height: 50px;
    border-radius: 12px;
    right: 20px;
    left: auto;
    transform: none;
  }
  to {
    width: 400px;
    height: 600px;
    border-radius: 12px;
    right: 20px;
    left: auto;
    transform: none;
  }
`;

const expandFromRectangleMobile = keyframes`
  from {
    width: calc(100vw - 20px);
    height: 50px;
    border-radius: 12px;
    left: 10px;
    right: 10px;
    transform: none;
  }
  to {
    width: calc(100vw - 20px);
    height: calc(100vh - 40px);
    border-radius: 12px;
    left: 10px;
    right: 10px;
    transform: none;
  }
`;

const collapseToCircle = keyframes`
  from {
    width: 400px;
    height: 600px;
    border-radius: 12px;
  }
  to {
    width: 70px;
    height: 70px;
    border-radius: 50%;
  }
`;

const collapseToCircleMobile = keyframes`
  from {
    width: calc(100vw - 20px);
    height: calc(100vh - 40px);
    border-radius: 12px;
  }
  to {
    width: 60px;
    height: 60px;
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
    background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.nestleGray} 100%)`,
    border: `1px solid ${colors.primary}`,
    boxShadow: shadows.nestle,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    [mediaQueries.mobile]: {
      bottom: '10px',
      right: '10px',
      left: '10px',
      boxShadow: shadows.mobile,
    },
  };

  switch (chatState) {
    case 'circle':
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        cursor: 'pointer',
        [mediaQueries.mobile]: {
          width: '60px',
          height: '60px',
          position: 'fixed',
          right: '10px',
          left: 'auto',
        },
        '&:hover': {
          transform: 'scale(1.08)',
          boxShadow: shadows.gold,
        },
        [mediaQueries.touchDevice]: {
          '&:hover': {
            transform: 'none',
            boxShadow: shadows.nestle,
          },
          '&:active': {
            transform: 'scale(0.95)',
          },
        },
      };
    
    case 'expanding':
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        animation: `${expandToWindow} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        [mediaQueries.mobile]: {
          width: '60px',
          height: '60px',
          animation: `${expandToWindowMobile} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
          position: 'fixed',
          right: '10px',
          left: 'auto',
        },
      };
    
    case 'open':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '12px',
        [mediaQueries.mobile]: {
          width: 'calc(100vw - 20px)',
          height: 'calc(100vh - 40px)',
          top: '10px',
          bottom: '10px',
          left: '10px',
          right: '10px',
        },
      };
    
    case 'collapsing':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '12px',
        animation: `${collapseToRectangle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        [mediaQueries.mobile]: {
          width: 'calc(100vw - 20px)',
          height: 'calc(100vh - 40px)',
          animation: `${collapseToRectangleMobile} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        },
      };
    
    case 'collapsed':
      return {
        ...baseStyles,
        width: '400px',
        height: '50px',
        borderRadius: '12px',
        cursor: 'pointer',
        right: '20px',
        left: 'auto',
        transform: 'none',
        [mediaQueries.mobile]: {
          width: 'calc(100vw - 20px)',
          height: '50px',
          left: '10px',
          right: '10px',
          transform: 'none',
        },
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: shadows.gold,
          [mediaQueries.mobile]: {
            transform: 'none',
          },
        },
        [mediaQueries.touchDevice]: {
          '&:hover': {
            transform: 'none',
            boxShadow: shadows.nestle,
          },
          '&:active': {
            transform: 'scale(0.98)',
          },
        },
      };
    
    case 'expanding-from-rectangle':
      return {
        ...baseStyles,
        width: '400px',
        height: '50px',
        borderRadius: '12px',
        animation: `${expandFromRectangle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        [mediaQueries.mobile]: {
          width: 'calc(100vw - 20px)',
          height: '50px',
          animation: `${expandFromRectangleMobile} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        },
      };
    
    case 'closing':
      return {
        ...baseStyles,
        width: '400px',
        height: '600px',
        borderRadius: '12px',
        animation: `${collapseToCircle} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        [mediaQueries.mobile]: {
          width: 'calc(100vw - 20px)',
          height: 'calc(100vh - 40px)',
          animation: `${collapseToCircleMobile} 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards`,
        },
      };
    
    default:
      return {
        ...baseStyles,
        width: '70px',
        height: '70px',
        borderRadius: '50%',
        [mediaQueries.mobile]: {
          width: '60px',
          height: '60px',
        },
      };
  }
});

const CircleContent = styled(Box)({
  width: '100%',
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
});

const ExpandingContent = styled(FlexCenter)({
  color: colors.white,
  width: '100%',
  height: '100%',
  flexDirection: 'column',
  gap: 12,
  [mediaQueries.mobile]: {
    gap: 8,
  },
});

const SmartieText = styled(Typography)(({ size = 'normal' }) => ({
  fontSize: size === 'small' ? 10 : 7,
  fontWeight: 700,
  letterSpacing: '0.8px',
  textAlign: 'center',
  color: colors.nestleCream,
  fontFamily,
  textShadow: '0 1px 2px rgba(0,0,0,0.3)',
  [mediaQueries.mobile]: {
    fontSize: size === 'small' ? 9 : 6,
    letterSpacing: '0.6px',
  },
}));

const CollapsedContent = styled(FlexCenter)({
  gap: 12,
  color: colors.white,
  width: '100%',
  height: '100%',
  animation: `${fadeInContent} 0.2s ease 0.1s both`,
  [mediaQueries.mobile]: {
    gap: 8,
  },
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
    } else if (state === 'expanding' || state === 'expanding-from-rectangle') {
      return (
        <ExpandingContent>
          <ExpandingNestleLogo 
            src={nestleLogo} 
            alt="Nestlé Logo"
            loading="lazy"
          />
        </ExpandingContent>
      );
    } else if (state === 'collapsing') {
      return (
        <CollapsedContent>
          <CollapsedNestleLogo 
            src={nestleLogoCircle} 
            alt="Nestlé Logo"
            loading="lazy"
          />
          <SmartieText size="small">SMARTIE - CLICK TO EXPAND</SmartieText>
        </CollapsedContent>
      );
    } else if (state === 'closing') {
      return (
        <CircleContent>
          <ClosingNestleLogo 
            src={nestleLogoCircle} 
            alt="Nestlé Logo"
            loading="lazy"
          />
        </CircleContent>
      );
    } else if (state === 'collapsed') {
      return (
        <CollapsedContent>
          <CollapsedNestleLogo 
            src={nestleLogoCircle} 
            alt="Nestlé Logo"
            loading="lazy"
          />
          <SmartieText size="small">SMARTIE - CLICK TO EXPAND</SmartieText>
        </CollapsedContent>
      );
    } else {
      return (
        <CircleContent>
          <FloatingNestleLogo 
            src={nestleLogoCircle} 
            alt="Nestlé Logo"
            loading="lazy"
          />
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