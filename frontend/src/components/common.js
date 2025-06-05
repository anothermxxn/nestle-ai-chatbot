import { styled } from '@mui/material/styles';
import { Box, IconButton } from '@mui/material';

// Nestlé brand colors
export const colors = {
  primary: '#726050',
  nestleWhite: '#e7ecea',
  nestleCream: '#afa89b',
  nestleGray: '#242525',
  nestleBlue: '#16678c',
  // UI colors
  white: '#ffffff',
  gray100: '#f5f5f5',
  gray200: '#eeeeee',
  gray500: '#9e9e9e',
  gray600: '#757575',
  gray800: '#424242',
};

// Nestlé brand font family
export const fontFamily = "'Helvetica Neue', Helvetica, Arial, sans-serif";

export const StyledIconButton = styled(IconButton)(({ variant = 'default' }) => ({
  padding: 4,
  borderRadius: 6,
  fontFamily,
  transition: 'all 0.2s ease',
  ...(variant === 'header' && {
    color: colors.nestleCream,
    '&:hover': {
      backgroundColor: 'rgba(175, 168, 155, 0.15)',
      transform: 'scale(1.05)',
    },
  }),
  ...(variant === 'send' && {
    width: 32,
    height: 32,
    background: colors.primary,
    color: colors.white,
    border: `1px solid ${colors.nestleCream}`,
    '&:hover': {
      background: colors.primary,
      color: colors.nestleGray,
      opacity: 1,
      transform: 'scale(1.08)',
      boxShadow: `0 4px 12px ${colors.nestleCream}40`,
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
}; 