import { styled } from '@mui/material/styles';
import { Box, IconButton } from '@mui/material';

// Nestlé brand colors
export const colors = {
  primary: '#726050',
  nestleCream: '#afa89b',
  nestleGray: '#242525',
  // UI colors
  white: '#ffffff',
  gray100: '#f5f5f5',
  gray200: '#eeeeee',
  gray500: '#9e9e9e',
  gray600: '#757575',
  gray800: '#424242',
};

// Mobile breakpoints
export const breakpoints = {
  mobile: 480,
  tablet: 768,
  desktop: 1024,
};

// Media queries
export const mediaQueries = {
  mobile: `@media (max-width: ${breakpoints.mobile}px)`,
  tablet: `@media (max-width: ${breakpoints.tablet}px)`,
  desktop: `@media (min-width: ${breakpoints.desktop}px)`,
  touchDevice: '@media (hover: none) and (pointer: coarse)',
};

export const fontFamily = "'Helvetica Neue', Helvetica, Arial, sans-serif";

export const StyledIconButton = styled(IconButton)(({ variant = 'default' }) => ({
  padding: 4,
  borderRadius: 6,
  fontFamily,
  transition: 'all 0.2s ease',
  [mediaQueries.mobile]: {
    padding: 8,
    minWidth: 44,
    minHeight: 44,
  },
  [mediaQueries.touchDevice]: {
    '&:active': {
      transform: 'scale(0.95)',
    },
  },
  ...(variant === 'header' && {
    color: colors.nestleCream,
    '&:hover': {
      backgroundColor: 'rgba(175, 168, 155, 0.15)',
      transform: 'scale(1.05)',
    },
    [mediaQueries.touchDevice]: {
      '&:hover': {
        backgroundColor: 'transparent',
        transform: 'none',
      },
      '&:active': {
        backgroundColor: 'rgba(175, 168, 155, 0.25)',
        transform: 'scale(0.95)',
      },
    },
  }),
  ...(variant === 'send' && {
    width: 32,
    height: 32,
    background: colors.primary,
    color: colors.white,
    border: `1px solid ${colors.nestleCream}`,
    [mediaQueries.mobile]: {
      width: 40,
      height: 40,
    },
    '&:hover': {
      background: colors.primary,
      color: colors.nestleGray,
      transform: 'scale(1.08)',
      boxShadow: `0 4px 12px ${colors.nestleCream}40`,
    },
    [mediaQueries.touchDevice]: {
      '&:hover': {
        background: colors.primary,
        color: colors.white,
        transform: 'none',
        boxShadow: 'none',
      },
      '&:active': {
        background: colors.nestleGray,
        transform: 'scale(0.95)',
        boxShadow: `0 2px 8px ${colors.nestleCream}60`,
      },
    },
    '&:disabled': {
      background: colors.nestleGray,
      color: colors.nestleCream,
      border: `1px solid ${colors.nestleCream}`,
      opacity: 1,
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

export const NestleHeader = styled(Box)({
  background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.nestleGray} 100%)`,
  color: colors.white,
  fontFamily,
});

// Shadows
export const shadows = {
  light: '0 1px 3px rgba(99, 81, 61, 0.12)',
  nestle: '0 6px 24px rgba(99, 81, 61, 0.2)',
  gold: '0 4px 16px rgba(212, 175, 55, 0.25)',
  mobile: '0 4px 16px rgba(99, 81, 61, 0.15)',
}; 