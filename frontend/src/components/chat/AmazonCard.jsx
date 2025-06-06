import { Box, Typography, Paper, Rating } from '@mui/material';
import { styled } from '@mui/material/styles';
import { ShoppingCart, Star, StarBorder } from '@mui/icons-material';
import { colors, fontFamily, mediaQueries, rgba } from '../common';

const AmazonCardContainer = styled(Paper)({
  width: 150,
  height: 200,
  borderRadius: 12,
  background: colors.nestleBackground,
  boxShadow: `0 4px 12px ${rgba(colors.primary, 0.15)}`,
  transition: 'all 0.2s ease',
  fontFamily,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
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
    height: 210,
    borderRadius: 10,
  },
  [mediaQueries.touchDevice]: {
    '&:active': {
      transform: 'scale(0.98)',
    },
  },
});

const ProductImageContainer = styled(Box)({
  width: '100%',
  height: 150,
  position: 'relative',
  overflow: 'hidden',
  [mediaQueries.mobile]: {
    height: 160,
  },
});

const ProductImage = styled('img')({
  width: '100%',
  height: '100%',
  objectFit: 'contain',
  background: colors.white,
});

const ProductInfo = styled(Box)({
  padding: '12px',
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  [mediaQueries.mobile]: {
    padding: '10px',
  },
});

const ProductTitle = styled(Typography)({
  fontSize: 14,
  fontWeight: 600,
  color: colors.primary,
  fontFamily,
  lineHeight: 1.2,
  marginBottom: 6,
  wordBreak: 'break-word',
  hyphens: 'auto',
  minHeight: '16px',
  maxHeight: '48px',
  overflow: 'hidden',
  display: '-webkit-box',
  WebkitLineClamp: 3,
  WebkitBoxOrient: 'vertical',
  '@supports not (-webkit-line-clamp: 3)': {
    display: 'block',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxHeight: '16px',
  },
  [mediaQueries.mobile]: {
    fontSize: 15,
    lineHeight: 1.3,
    marginBottom: 4,
    minHeight: '18px',
    maxHeight: '54px',
    '@supports not (-webkit-line-clamp: 3)': {
      maxHeight: '18px',
    },
  },
});

const ProductPrice = styled(Typography)({
  fontSize: 14,
  fontWeight: 700,
  color: colors.nestleCream,
  fontFamily,
  marginBottom: 4,
  [mediaQueries.mobile]: {
    fontSize: 16,
    marginBottom: 3,
  },
});

const RatingContainer = styled(Box)({
  position: 'absolute',
  top: 8,
  right: 8,
  background: colors.primary,
  padding: '2px 6px',
  borderRadius: 4,
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  [mediaQueries.mobile]: {
    gap: 3,
  },
});

const StyledStar = styled(Star)({
  fontSize: '14px',
  color: colors.white,
  [mediaQueries.mobile]: {
    fontSize: '16px',
  },
});

const StyledStarBorder = styled(StarBorder)({
  fontSize: '14px',
  color: colors.gray500,
  [mediaQueries.mobile]: {
    fontSize: '16px',
  },
});

const PlaceholderImage = styled(Box)({
  width: '100%',
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: colors.gray200,
});

/**
 * Amazon product card component with product preview and purchase link
 * @param {Object} product - Product data object
 * @param {string} product.title - Product title
 * @param {string} product.image_url - Product image URL
 * @param {string} product.price - Product price
 * @param {string} product.rating - Product rating
 * @param {number} product.reviewCount - Number of reviews
 * @param {string} product.product_url - Amazon product URL
 * @returns {JSX.Element} The styled Amazon product card component
 */
const AmazonCard = ({ product }) => {
  /**
   * Formats and validates the product title
   * @param {string} title - Raw title string
   * @returns {string} Formatted title string
   */
  const formatTitle = (title) => {
    if (!title || typeof title !== 'string') {
      return 'Product Available';
    }

    // Clean up common issues
    let cleaned = title.trim();
    cleaned = cleaned.replace(/&amp;/g, '&')
                     .replace(/&lt;/g, '<')
                     .replace(/&gt;/g, '>')
                     .replace(/&quot;/g, '"')
                     .replace(/&#39;/g, "'");
    cleaned = cleaned.replace(/,\s*$/, '');
    cleaned = cleaned.replace(/\s+/g, ' ');
    
    if (cleaned.length < 8 && cleaned.toLowerCase() === 'nestle') {
      cleaned = 'Nestlé Product';
    }

    return cleaned || 'Product Available';
  };

  /**
   * Formats price string for consistent display
   * @param {string} price - Raw price string
   * @returns {string} Formatted price string
   */
  const formatPrice = (price) => {
    if (!price) return 'Price unavailable';
    return price.trim().startsWith('$') ? price.trim() : `$${price.trim()}`;
  };

  /**
   * Parses rating from backend format "X.X/5" to numeric value
   * @param {string} rating - Rating in "X.X/5" format
   * @returns {number|null} Numeric rating value or null if invalid
   */
  const parseRating = (rating) => {
    if (!rating) return null;
    if (typeof rating === 'number') return rating;
    if (typeof rating === 'string' && rating.includes('/')) {
      return parseFloat(rating.split('/')[0]);
    }
    return parseFloat(rating) || null;
  };

  const numericRating = parseRating(product.rating);
  const displayTitle = formatTitle(product.title);

  return (
    <AmazonCardContainer
      component="a"
      href={product.product_url}
      target="_blank"
      rel="noopener noreferrer"
      elevation={0}
    >
      <ProductImageContainer>
        {numericRating && numericRating > 0 && (
          <RatingContainer>
            <Rating
              value={numericRating}
              readOnly
              precision={0.1}
              icon={<StyledStar />}
              emptyIcon={<StyledStarBorder />}
            />
          </RatingContainer>
        )}

        {product.image_url ? (
          <ProductImage
            src={product.image_url}
            alt={displayTitle}
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : (
          <PlaceholderImage>
            <ShoppingCart sx={{ fontSize: 32, color: colors.gray500 }} />
          </PlaceholderImage>
        )}
        
        <PlaceholderImage style={{ display: 'none' }}>
          <ShoppingCart sx={{ fontSize: 32, color: colors.gray500 }} />
        </PlaceholderImage>
      </ProductImageContainer>

      <ProductInfo>
        <Box>
          <ProductTitle>{displayTitle}</ProductTitle>
          
          <ProductPrice>{formatPrice(product.price)}</ProductPrice>
        </Box>
      </ProductInfo>
    </AmazonCardContainer>
  );
};

export default AmazonCard; 