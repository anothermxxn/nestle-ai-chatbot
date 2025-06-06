import { useState, useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import { styled, keyframes } from '@mui/material/styles';
import ChatWindow from './ChatWindow';
import { colors, fontFamily, FlexCenter, shadows, mediaQueries, rgba } from '../common';
import { validateFSA } from '../../lib/utils/validation';
import { ipToCoordinates, fsaToCoordinates } from '../../lib/utils/geocoding';

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
  boxShadow: `0 2px 8px ${rgba(colors.primary, 0.3)}`,
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
  boxShadow: `0 2px 8px ${rgba(colors.primary, 0.3)}`,
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
  boxShadow: `0 8px 32px rgba(${colors.primary}, 0.3)`,
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
          boxShadow: shadows.nestle,
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
          boxShadow: shadows.nestle,
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
  textShadow: `0 1px 2px ${rgba(colors.black, 0.3)}`,
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
  const [location, setLocation] = useState({
    coords: null,
    fsa: null,
    error: null,
    loading: false,
    permission: null, // 'granted', 'denied', 'prompt'
    source: null, // 'auto', 'manual', 'ip'
    city: null,
    region: null
  });

  const geolocationAttempted = useRef(false);

  // Initialize location on component mount
  useEffect(() => {
    if (geolocationAttempted.current) return;
    
    const hasStoredLocation = loadStoredLocation();
    
    if (!hasStoredLocation) {
      geolocationAttempted.current = true;
      tryGeolocationWithFallbacks();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Gets the FSA (first 3 characters of postal code) from coordinates using reverse geocoding
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<string>} FSA (Forward Sortation Area)
   */
  const getFSAFromCoords = async (lat, lon) => {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`
    ).catch(() => null);
    
    if (!response?.ok) return 'LOC';
    
    const data = await response.json().catch(() => ({}));
    const fullPostalCode = data.address?.postcode;
    
    if (fullPostalCode) {
      const cleanedPostalCode = fullPostalCode.replace(/[\s-]/g, '');
      const fsa = cleanedPostalCode.substring(0, 3).toUpperCase();
      
      if (validateFSA(fsa)) {
        return fsa;
      }
    }
    
    return 'LOC';
  };

  /**
   * Get location (both coordinates and FSA) from IP address
   * @returns {Promise<{coords: {latitude: number, longitude: number}, fsa: string, city?: string, region?: string} | null>} Location data or null
   */
  const getLocationFromIP = async () => {
    try {
      // Get coordinates directly from IP
      const ipLocation = await ipToCoordinates();
      
      if (!ipLocation) {
        return null;
      }
      
      // Get FSA from reverse geocoding using the coordinates
      let fsa = 'LOC'; // Default fallback
      
      try {
        const reverseFsa = await getFSAFromCoords(ipLocation.lat, ipLocation.lon);
        if (reverseFsa && reverseFsa !== 'LOC') {
          fsa = reverseFsa;
        }
      } catch {
        // Silent fallback if reverse geocoding fails
      }
      
      return {
        coords: {
          latitude: ipLocation.lat,
          longitude: ipLocation.lon
        },
        fsa: fsa,
        city: ipLocation.city,
        region: ipLocation.region
      };
      
    } catch (error) {
      console.error('Error getting location from IP:', error);
      return null;
    }
  };

  /**
   * Multi-strategy geolocation
   */
  const tryGeolocationWithFallbacks = async () => {
    if (!navigator.geolocation) {
      setLocation(prev => ({
        ...prev,
        error: 'Geolocation is not supported by this browser',
        loading: false
      }));
      return;
    }

    setLocation(prev => ({ ...prev, loading: true, error: null }));

    // High accuracy GPS
    const tryHighAccuracy = () => new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000
      });
    });

    // Network-based positioning
    const tryNetworkPositioning = () => new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 15000,
        maximumAge: 600000
      });
    });

    try {
      // Try high accuracy first, fallback to network positioning
      let position;
      try {
        position = await tryHighAccuracy();
      } catch (error) {
        if (error.code === error.PERMISSION_DENIED) {
          throw error;
        }
        position = await tryNetworkPositioning();
      }

      // Process successful position
      const { latitude, longitude } = position.coords;
      
      const fsa = await getFSAFromCoords(latitude, longitude);
      const locationData = {
        coords: { latitude, longitude },
        fsa,
        error: null,
        loading: false,
        permission: 'granted',
        source: 'auto'
      };
      
      setLocation(locationData);
      localStorage.setItem('location', JSON.stringify({
        ...locationData,
        timestamp: Date.now()
      }));
      return;
    } catch (geoError) {
      if (geoError.code === geoError.PERMISSION_DENIED) {
        setLocation(prev => ({
          ...prev,
          error: 'Location access denied. You can set your location manually.',
          loading: false,
          permission: 'denied'
        }));
        return;
      }
    }

    // Fallback to IP-based location
    const ipLocation = await getLocationFromIP();
    if (ipLocation) {
      const locationData = {
        coords: ipLocation.coords,
        fsa: ipLocation.fsa,
        error: null,
        loading: false,
        permission: 'granted',
        source: 'ip',
        city: ipLocation.city,
        region: ipLocation.region
      };
      
      setLocation(locationData);
      localStorage.setItem('location', JSON.stringify({
        ...locationData,
        timestamp: Date.now()
      }));
      return;
    }

    // All strategies failed
    setLocation(prev => ({
      ...prev,
      error: 'Location detection failed. Please set manually.',
      loading: false,
      permission: 'granted'
    }));
  };

  /**
   * Handles manual location entry
   * @param {string} fsaCode - Manual FSA input (3 character postal code)
   */
  const setManualLocation = async (fsaCode) => {
    // Try to get coordinates for the manual FSA entry for better store lookup
    let coords = null;
    
    try {
      const fsaCoords = await fsaToCoordinates(fsaCode);
      if (fsaCoords) {
        coords = {
          latitude: fsaCoords.lat,
          longitude: fsaCoords.lon
        };
      }
    } catch (error) {
      console.warn(`Could not get coordinates for FSA ${fsaCode}:`, error);
    }
    
    const locationData = {
      coords: coords,
      fsa: fsaCode,
      error: null,
      loading: false,
      permission: location.permission,
      source: 'manual'
    };
    
    setLocation(locationData);
    localStorage.setItem('location', JSON.stringify({
      ...locationData,
      timestamp: Date.now()
    }));
  };

  /**
   * Loads location from localStorage on component mount
   */
  const loadStoredLocation = () => {
    const stored = localStorage.getItem('location');
    if (!stored) return false;
    
    try {
      const locationData = JSON.parse(stored);
      const timeDiff = Date.now() - (locationData.timestamp || 0);
      
      // Use stored location if less than 24 hour old
      if (timeDiff < 86400000) {
        setLocation({
          coords: locationData.coords,
          fsa: locationData.fsa,
          error: null,
          loading: false,
          permission: locationData.permission || null,
          source: locationData.source || 'auto',
          city: locationData.city || null,
          region: locationData.region || null
        });
        return true;
      }
    } catch {
      // Invalid JSON in localStorage
    }
    
    return false;
  };

  /**
   * Gets the user's current location using multi-strategy approach
   */
  const getCurrentLocation = () => {
    tryGeolocationWithFallbacks();
  };

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
   */
  const handleClose = () => {
    setState('closing');
    setTimeout(() => setState('circle'), 400);
    
    // Signal ChatWindow to reset the conversation
    setResetTrigger(prev => prev + 1);
  };

  /**
   * Renders appropriate content based on current chat window state
   * @returns {JSX.Element} Content for the current state
   */
  const renderContent = () => {
    // Keep ChatWindow mounted for all states except circle/closing to preserve conversation
    const shouldShowChatWindow = ['open', 'collapsing', 'collapsed', 'expanding-from-rectangle'].includes(state);
    
    if (shouldShowChatWindow) {
      return (
        <ChatWindowContent>
          <ChatWindow 
            onClose={handleClose} 
            onCollapse={handleCollapse}
            resetTrigger={resetTrigger}
            location={location}
            onLocationRefresh={getCurrentLocation}
            onLocationUpdate={setManualLocation}
            style={{
              display: state === 'open' ? 'flex' : 'none'
            }}
          />
          {/* Show collapsed UI overlay when needed */}
          {(state === 'collapsing' || state === 'collapsed') && (
            <CollapsedContent>
              <CollapsedNestleLogo 
                src="/logoCircle.jpg" 
                alt="Nestlé Logo"
                loading="lazy"
              />
              <SmartieText size="small">SMARTIE - CLICK TO EXPAND</SmartieText>
            </CollapsedContent>
          )}
          {/* Show expanding UI overlay when needed */}
          {state === 'expanding-from-rectangle' && (
            <ExpandingContent>
              <ExpandingNestleLogo 
                src="/logo.jpg" 
                alt="Nestlé Logo"
                loading="lazy"
              />
            </ExpandingContent>
          )}
        </ChatWindowContent>
      );
    } else if (state === 'expanding') {
      return (
        <ExpandingContent>
          <ExpandingNestleLogo 
            src="/logo.jpg" 
            alt="Nestlé Logo"
            loading="lazy"
          />
        </ExpandingContent>
      );
    } else if (state === 'closing') {
      return (
        <CircleContent>
          <ClosingNestleLogo 
            src="/logoCircle.jpg" 
            alt="Nestlé Logo"
            loading="lazy"
          />
        </CircleContent>
      );
    } else {
      return (
        <CircleContent>
          <FloatingNestleLogo 
            src="/logoCircle.jpg" 
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