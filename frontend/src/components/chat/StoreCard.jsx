import { Box, Typography, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';
import { LocationOn, Phone, AccessTime } from '@mui/icons-material';
import { colors, fontFamily, mediaQueries, rgba } from '../common';

const StoreCardContainer = styled(Paper)({
  width: 150,
  height: 150,
  padding: '12px',
  borderRadius: 12,
  background: colors.nestleBackground,
  boxShadow: `0 4px 12px ${rgba(colors.primary, 0.15)}`,
  transition: 'all 0.2s ease',
  fontFamily,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  flexShrink: 0,
  cursor: 'pointer',
  textDecoration: 'none',
  color: 'inherit',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: `0 8px 24px ${rgba(colors.primary, 0.25)}`,
    textDecoration: 'none',
    color: 'inherit',
  },
  '&:visited': {
    color: 'inherit',
  },
  [mediaQueries.mobile]: {
    width: 160,
    height: 160,
    padding: '12px',
    borderRadius: 10,
  },
  [mediaQueries.touchDevice]: {
    '&:active': {
      transform: 'scale(0.98)',
    },
  },
});

const StoreHeader = styled(Box)({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  marginBottom: 10,
  [mediaQueries.mobile]: {
    marginBottom: 8,
  },
});

const StoreName = styled(Typography)({
  fontSize: 16,
  fontWeight: 700,
  color: colors.primary,
  fontFamily,
  lineHeight: 1.2,
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  [mediaQueries.mobile]: {
    fontSize: 18,
  },
});

const DistanceChip = styled(Box)({
  background: colors.primary,
  color: colors.white,
  padding: '3px 8px',
  borderRadius: 6,
  fontSize: 12,
  fontWeight: 600,
  fontFamily,
  minWidth: 'fit-content',
  [mediaQueries.mobile]: {
    fontSize: 14,
    padding: '4px 8px',
    borderRadius: 6,
  },
});

const StoreInfoRow = styled(Box)({
  display: 'flex',
  alignItems: 'flex-start',
  gap: 5,
  marginBottom: 5,
  fontSize: 16,
  color: colors.nestleCream,
  fontFamily,
  [mediaQueries.mobile]: {
    fontSize: 18,
    gap: 8,
    marginBottom: 5,
  },
});

const StoreIcon = styled(Box)({
  width: 16,
  height: 16,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: colors.nestleCream,
  flexShrink: 0,
  lineHeight: 1,
  [mediaQueries.mobile]: {
    width: 18,
    height: 18,
  },
});

const StoreInfoText = styled(Typography)({
  fontSize: 13,
  fontFamily,
  flex: 1,
  lineHeight: 1.3,
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
  margin: 0,
  padding: 0,
  [mediaQueries.mobile]: {
    fontSize: 15,
  },
});

/**
 * Store card component displaying store information with Google Maps integration
 * @param {Object} store - Store data object
 * @param {string} store.name - Store name
 * @param {string} store.address - Store address
 * @param {string} store.distance - Distance from user location
 * @param {string} store.hours - Store operating hours
 * @param {string} store.phone - Store phone number
 * @param {number} store.lat - Store latitude coordinate
 * @param {number} store.lon - Store longitude coordinate
 * @returns {JSX.Element} The styled store card component
 */
const StoreCard = ({ store }) => {
  /**
   * Generates Google Maps URL for directions to the store
   * @returns {string} Google Maps directions URL
   */
  const getDirectionsUrl = () => {
    // Use the scraped Google Maps URL if available
    if (store.url) {
      return store.url;
    }
    
    // Fallback to generating search URL with specific location information
    if (store.lat && store.lon) {
      // Use search format with store name and address for better targeting
      const searchQuery = store.address 
        ? `${store.name}, ${store.address}`
        : `${store.name} near ${store.lat},${store.lon}`;
      return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(searchQuery)}`;
    }
    
    // Final fallback to address search
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(store.address)}`;
  };

  /**
   * Formats phone number for display
   * @param {string} phone - Raw phone number
   * @returns {string} Formatted phone number
   */
  const formatPhone = (phone) => {
    if (!phone) return '';
    // Remove non-numeric characters
    const cleaned = phone.replace(/\D/g, '');
    // Format as (XXX) XXX-XXXX
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
  };

  return (
    <StoreCardContainer
      component="a"
      href={getDirectionsUrl()}
      target="_blank"
      rel="noopener noreferrer"
      elevation={0}
    >
      <Box>
        <StoreHeader>
          <StoreName>{store.name}</StoreName>
          <DistanceChip>{store.distance}</DistanceChip>
        </StoreHeader>

        {store.hours && (
          <StoreInfoRow>
            <StoreIcon>
              <AccessTime sx={{ fontSize: 'inherit' }} />
            </StoreIcon>
            <StoreInfoText>
              {store.hours}
            </StoreInfoText>
          </StoreInfoRow>
        )}

        {store.phone && (
          <StoreInfoRow>
            <StoreIcon>
              <Phone sx={{ fontSize: 'inherit' }} />
            </StoreIcon>
            <StoreInfoText>
              {formatPhone(store.phone)}
            </StoreInfoText>
          </StoreInfoRow>
        )}

        <StoreInfoRow>
          <StoreIcon>
            <LocationOn sx={{ fontSize: 'inherit' }} />
          </StoreIcon>
          <StoreInfoText>
            {store.address}
          </StoreInfoText>
        </StoreInfoRow>
      </Box>
    </StoreCardContainer>
  );
};

export default StoreCard; 