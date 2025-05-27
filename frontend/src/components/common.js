import { styled } from '@mui/material/styles';
import { Box, Avatar, IconButton } from '@mui/material';

// Common theme colors
export const colors = {
  primary: '#1e4d8b',
  white: '#ffffff',
  gray50: '#f8fafc',
  gray100: '#f1f5f9',
  gray200: '#e2e8f0',
  gray300: '#cbd5e1',
  gray400: '#94a3b8',
  gray500: '#64748b',
  gray600: '#475569',
};

// Common font family
export const fontFamily = "'Avenir Next', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

// Common styled components
export const StyledAvatar = styled(Avatar)(({ size = 'medium' }) => {
  const sizeMap = {
    small: { width: 24, height: 24, fontSize: 14 },
    medium: { width: 32, height: 32, fontSize: 18 },
    large: { width: 36, height: 36, fontSize: 20 },
  };
  
  return {
    width: sizeMap[size].width,
    height: sizeMap[size].height,
    background: colors.primary,
    color: colors.white,
    fontSize: sizeMap[size].fontSize,
    fontFamily,
    fontWeight: 600,
  };
});

export const StyledIconButton = styled(IconButton)(({ variant = 'default' }) => ({
  padding: 4,
  borderRadius: 4,
  fontFamily,
  ...(variant === 'header' && {
    color: colors.white,
    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
  }),
  ...(variant === 'send' && {
    width: 28,
    height: 28,
    background: colors.gray500,
    color: colors.white,
    '&:hover': {
      background: colors.gray600,
      transform: 'scale(1.05)',
    },
    '&:focus': {
      background: colors.primary,
      outline: 'none',
    },
    '&:disabled': {
      background: colors.gray400,
      color: colors.white,
    },
  }),
}));

export const FlexCenter = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
});

export const FlexBetween = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
});

// Common animations
export const commonTransitions = {
  smooth: 'all 0.2s ease',
  bounce: 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
};

// Common shadows
export const shadows = {
  light: '0 1px 3px rgba(0, 0, 0, 0.1)',
  medium: '0 4px 20px rgba(0, 0, 0, 0.15)',
  heavy: '0 8px 32px rgba(0, 0, 0, 0.15)',
}; 