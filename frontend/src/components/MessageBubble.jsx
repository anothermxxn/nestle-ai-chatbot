import { Box, Typography, Paper, Chip, Tooltip, Link } from '@mui/material';
import { styled } from '@mui/material/styles';
import { forwardRef } from 'react';
import { colors, fontFamily, mediaQueries, rgba } from './common';
import { parseMessageContent, formatReferenceTooltip } from '../utils/messageFormatter';

// Import Nestlé logo
import nestleLogoCircle from '../assets/logoCircle.jpg';

// Styled components
const MessageContainer = styled(Box)(({ messagetype }) => ({
  display: 'flex',
  margin: '12px 0',
  maxWidth: '95%',
  fontFamily,
  fontWeight: 600,
  justifyContent: messagetype === 'user' ? 'flex-end' : 'flex-start',
  alignItems: messagetype === 'user' ? 'center' : 'flex-start',
  gap: messagetype === 'user' ? 0 : 12,
  position: messagetype === 'user' ? 'static' : 'relative',
  marginLeft: messagetype === 'user' ? 'auto' : 0,
  [mediaQueries.mobile]: {
    margin: '10px 0',
    maxWidth: '98%',
    gap: messagetype === 'user' ? 0 : 10,
    justifyContent: messagetype === 'user' ? 'flex-end' : 'flex-start',
    marginLeft: messagetype === 'user' ? 'auto' : 0,
  },
}));

const AssistantAvatar = styled(Box)({
  width: 36,
  height: 36,
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: colors.white,
  border: `1px solid ${colors.primary}`,
  boxShadow: `0 2px 8px ${rgba(colors.primary, 0.2)}`,
  flexShrink: 0,
  [mediaQueries.mobile]: {
    width: 32,
    height: 32,
  },
});

const NestleAvatarLogo = styled('img')({
  width: 30,
  height: 30,
  borderRadius: '50%',
  objectFit: 'cover',
  [mediaQueries.mobile]: {
    width: 26,
    height: 26,
  },
});

const MessageContent = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  flex: 1,
  minWidth: 0,
  [mediaQueries.mobile]: {
    gap: 6,
  },
});

const MessageText = styled(Paper)(({ messagetype }) => ({
  padding: '10px 14px',
  borderRadius: 12,
  fontSize: 14,
  lineHeight: 1.5,
  wordWrap: 'break-word',
  fontWeight: 500,
  fontFamily,
  background: messagetype === 'user' 
    ? colors.nestleGray
    : messagetype === 'system' 
    ? colors.gray200 
    : colors.white,
  color: messagetype === 'user' 
    ? colors.nestleCream 
    : messagetype === 'system' 
    ? colors.gray600 
    : colors.nestleCream,
  border: messagetype === 'user' 
    ? `1px solid ${colors.nestleCream}` 
    : 'none',
  borderBottomRightRadius: messagetype === 'user' ? 4 : 12,
  borderBottomLeftRadius: messagetype === 'assistant' ? 4 : 12,
  boxShadow: messagetype === 'user' 
    ? 'none'
    : `0 4px 12px ${rgba(colors.primary, 0.2)}`,
  ...(messagetype === 'user' && {
    width: 'fit-content',
    maxWidth: '100%',
  }),
  [mediaQueries.mobile]: {
    padding: '8px 12px',
    fontSize: 16,
    borderRadius: 10,
    borderBottomRightRadius: messagetype === 'user' ? 3 : 10,
    borderBottomLeftRadius: messagetype === 'assistant' ? 3 : 10,
  },
  ...(messagetype === 'system' && {
    textAlign: 'center',
    fontStyle: 'italic',
    fontSize: 12,
    margin: '4px auto',
    maxWidth: '200px',
    [mediaQueries.mobile]: {
      fontSize: 14,
      maxWidth: '180px',
      margin: '3px auto',
    },
  }),
}));

const FormattedText = styled(Box)({
  fontSize: 14,
  lineHeight: 1.6,
  fontFamily,
  [mediaQueries.mobile]: {
    fontSize: 16,
    lineHeight: 1.5,
  },
});

const BoldText = styled('span')({
  fontWeight: 700,
});

const UnderlinedText = styled('span')({
  textDecoration: 'underline',
});

const BoldUnderlinedText = styled('span')({
  fontWeight: 700,
  textDecoration: 'underline',
});

const BulletList = styled(Box)({
  marginLeft: 16,
  marginTop: 4,
  marginBottom: 4,
  [mediaQueries.mobile]: {
    marginLeft: 12,
    marginTop: 3,
    marginBottom: 3,
  },
});

const BulletItem = styled(Box)({
  display: 'flex',
  alignItems: 'flex-start',
  marginBottom: 2,
  [mediaQueries.mobile]: {
    marginBottom: 1,
  },
  '&::before': {
    content: '"•"',
    color: colors.nestleCream,
    fontWeight: 'bold',
    width: 12,
    marginRight: 8,
    marginTop: 2,
    flexShrink: 0,
    [mediaQueries.mobile]: {
      width: 10,
      marginRight: 6,
      marginTop: 1,
    },
  },
});

const NumberedList = styled(Box)({
  marginLeft: 16,
  marginTop: 4,
  marginBottom: 4,
  [mediaQueries.mobile]: {
    marginLeft: 12,
    marginTop: 3,
    marginBottom: 3,
  },
});

const NumberedItem = styled(Box)(({ number }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  marginBottom: 2,
  [mediaQueries.mobile]: {
    marginBottom: 1,
  },
  '&::before': {
    content: `"${number}."`,
    color: colors.nestleCream,
    fontWeight: 'bold',
    minWidth: 24,
    marginRight: 8,
    marginTop: 2,
    flexShrink: 0,
    [mediaQueries.mobile]: {
      minWidth: 20,
      marginRight: 6,
      marginTop: 1,
    },
  },
}));

const StyledLink = styled(Link)({
  color: colors.nestleCream,
  textDecoration: 'underline',
  cursor: 'pointer',
  fontWeight: 600,
  '&:hover': {
    color: colors.white,
    textDecoration: 'underline',
  },
  [mediaQueries.touchDevice]: {
    '&:hover': {
      color: colors.nestleCream,
    },
    '&:active': {
      color: colors.white,
    },
  },
});

const ParagraphText = styled(Box)({
  marginBottom: 6,
  '&:last-child': {
    marginBottom: 0,
  },
  [mediaQueries.mobile]: {
    marginBottom: 4,
  },
});

const ReferencesContainer = styled(Box)({
  display: 'flex',
  flexWrap: 'wrap',
  gap: 6,
  marginTop: 10,
  alignItems: 'center',
  [mediaQueries.mobile]: {
    gap: 4,
    marginTop: 8,
  },
});

const ReferencesLabel = styled(Typography)({
  fontSize: 11,
  fontWeight: 700,
  color: colors.nestleCream,
  marginRight: 6,
  textTransform: 'uppercase',
  letterSpacing: '0.6px',
  fontFamily,
  [mediaQueries.mobile]: {
    fontSize: 10,
    marginRight: 4,
    letterSpacing: '0.4px',
  },
});

const ReferenceButton = styled(Chip)(() => ({
  backgroundColor: `${colors.nestleCream} !important`,
  color: `${colors.nestleGray} !important`,
  width: 22,
  height: 22,
  fontSize: 10,
  fontWeight: 700,
  cursor: 'pointer',
  transition: 'all 0.25s ease',
  border: 'none !important',
  minWidth: 22,
  [mediaQueries.mobile]: {
    width: 24,
    height: 24,
    fontSize: 9,
    minWidth: 24,
  },
  [mediaQueries.touchDevice]: {
    '&:hover': {
      backgroundColor: `${colors.nestleCream} !important`,
      transform: 'none',
    },
    '&:active': {
      backgroundColor: `${colors.nestleGray} !important`,
      color: `${colors.nestleCream} !important`,
      transform: 'scale(0.95)',
    },
  },
  '& .MuiChip-label': {
    padding: '0 !important',
    fontFamily,
    color: `${colors.nestleGray} !important`,
  },
}));

const StyledTooltip = styled(({ className, ...props }) => (
  <Tooltip {...props} classes={{ popper: className }} />
))({
  '& .MuiTooltip-tooltip': {
    backgroundColor: colors.gray800,
    color: colors.white,
    fontSize: 12,
    fontWeight: 500,
    fontFamily,
    padding: '10px 14px',
    borderRadius: 8,
    maxWidth: 280,
    boxShadow: `0 6px 20px ${rgba(colors.black, 0.2)}`,
    border: `1px solid ${colors.primary}`,
  },
  '& .MuiTooltip-arrow': {
    color: colors.gray800,
  },
});

const MessageTime = styled(Typography)(({ messagetype }) => ({
  fontSize: 11,
  color: colors.primary,
  marginTop: 4,
  textAlign: messagetype === 'user' ? 'right' : 'left',
  fontWeight: 500,
}));

/**
 * Renders a single text segment with appropriate formatting
 * @param {Object} segment - Text segment with type and content
 * @param {number} index - Index for React key
 * @returns {JSX.Element} Formatted text segment
 */
const renderTextSegment = (segment, index) => {
  const { type, content, appliedFormats = [] } = segment;
  
  // Determine which formatting to apply
  const isBold = appliedFormats.includes('bold') || type === 'bold';
  const isUnderlined = appliedFormats.includes('underline') || type === 'underline';
  const isLink = type === 'link';
  
  // Create the appropriate styled component
  const createStyledText = (text) => {
    if (isBold && isUnderlined) {
      return <BoldUnderlinedText>{text}</BoldUnderlinedText>;
    } else if (isBold) {
      return <BoldText>{text}</BoldText>;
    } else if (isUnderlined) {
      return <UnderlinedText>{text}</UnderlinedText>;
    }
    return text;
  };
  
  if (isLink) {
    return (
      <StyledLink 
        key={index}
        href={segment.url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
      >
        {createStyledText(content)}
      </StyledLink>
    );
  }
  
  // For non-link text, apply formatting if needed
  if (isBold || isUnderlined) {
    return <span key={index}>{createStyledText(content)}</span>;
  }
  
  // Plain text
  return content;
};

/**
 * Renders formatted message content with support for multiple formatting types
 * @param {Array} segments - Array of text segments from parseMessageContent
 * @param {Array} references - Array of reference objects for linking headers to sources
 * @returns {JSX.Element} Formatted text content
 */
const FormattedMessageContent = ({ segments, references = [] }) => {
  
  /**
   * Finds the best matching source URL for a given header text
   * @param {string} headerText - The header text to match
   * @returns {string|null} The URL of the best matching source, or null if no match
   */
  const findSourceUrlForHeader = (headerText) => {
    if (!references || !Array.isArray(references) || !headerText) {
      return null;
    }

    const headerLower = headerText.toLowerCase().trim();
    
    // Try to find exact or partial matches in title, section, or snippet
    for (const ref of references) {
      const title = (ref.title || '').toLowerCase();
      const section = (ref.section || ref.section_title || '').toLowerCase();
      
      // Check for exact matches first
      if (title === headerLower || section === headerLower) {
        return ref.url || ref.link || ref.source_url || ref.href;
      }
      
      // Check for partial matches (header contains key words from source)
      const headerWords = headerLower.split(' ').filter(word => word.length > 3);
      const titleWords = title.split(' ').filter(word => word.length > 3);
      const sectionWords = section.split(' ').filter(word => word.length > 3);
      
      // If header words significantly overlap with title or section words
      const titleMatches = headerWords.filter(word => titleWords.includes(word)).length;
      const sectionMatches = headerWords.filter(word => sectionWords.includes(word)).length;
      
      if (titleMatches >= Math.min(2, headerWords.length * 0.6) || 
          sectionMatches >= Math.min(2, headerWords.length * 0.6)) {
        return ref.url || ref.link || ref.source_url || ref.href;
      }
    }
    
    return null;
  };

  /**
   * Handles clicking on a header link
   * @param {string} url - The URL to open
   * @param {Event} event - The click event
   */
  const handleHeaderClick = (url, event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (url) {
      // Check if it's already a complete URL
      let fullUrl;
      if (url.startsWith('http://') || url.startsWith('https://')) {
        fullUrl = url;
      } else {
        // Prepend the base domain to the URL path
        fullUrl = `https://www.madewithnestle.ca/${url}`;
      }
      
      window.open(fullUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const renderSegment = (segment, index) => {
    switch (segment.type) {
      case 'header': {
        const sourceUrl = findSourceUrlForHeader(segment.content);
        
        if (sourceUrl) {
          // Render as clickable bold text
          return (
            <ParagraphText 
              key={index} 
              sx={{ cursor: 'pointer', marginTop: 1, marginBottom: 1 }}
              onClick={(event) => handleHeaderClick(sourceUrl, event)}
            >
              <StyledLink
                component="span"
                onClick={(event) => handleHeaderClick(sourceUrl, event)}
                sx={{ 
                  color: 'inherit',
                  textDecoration: 'underline',
                  fontWeight: 700,
                  '&:hover': {
                    color: colors.gray200,
                  }
                }}
              >
                {segment.content}
              </StyledLink>
            </ParagraphText>
          );
        } else {
          // Render as regular bold text
          return (
            <ParagraphText key={index} sx={{ marginTop: 1, marginBottom: 1 }}>
              <BoldText>{segment.content}</BoldText>
            </ParagraphText>
          );
        }
      }
      
      case 'bullet_group':
        return (
          <BulletList key={index}>
            {segment.items.map((item, itemIndex) => (
              <BulletItem key={itemIndex}>
                <Box>
                  {Array.isArray(item.content) 
                    ? item.content.map(renderTextSegment)
                    : item.content
                  }
                </Box>
              </BulletItem>
            ))}
          </BulletList>
        );
      
      case 'numbered_group':
        return (
          <NumberedList key={index}>
            {segment.items.map((item, itemIndex) => (
              <Box key={itemIndex}>
                <NumberedItem number={item.number}>
                  <Box>
                    {Array.isArray(item.content) 
                      ? item.content.map(renderTextSegment)
                      : item.content
                    }
                  </Box>
                </NumberedItem>
                {/* Render sub-bullets if they exist */}
                {item.subItems && item.subItems.length > 0 && (
                  <Box sx={{ marginLeft: 2, marginTop: 1 }}>
                    {item.subItems.map((subItem, subIndex) => (
                      <BulletItem key={subIndex}>
                        <Box>
                          {Array.isArray(subItem.content) 
                            ? subItem.content.map(renderTextSegment)
                            : subItem.content
                          }
                        </Box>
                      </BulletItem>
                    ))}
                  </Box>
                )}
              </Box>
            ))}
          </NumberedList>
        );
      
      case 'bullet':
        return (
          <BulletList key={index}>
            <BulletItem>
              <Box>
                {Array.isArray(segment.content) 
                  ? segment.content.map(renderTextSegment)
                  : segment.content
                }
              </Box>
            </BulletItem>
          </BulletList>
        );
      
      case 'numbered':
        return (
          <NumberedList key={index}>
            <NumberedItem number={segment.number}>
              <Box>
                {Array.isArray(segment.content) 
                  ? segment.content.map(renderTextSegment)
                  : segment.content
                }
              </Box>
            </NumberedItem>
          </NumberedList>
        );
      
      case 'linebreak':
        return <Box key={index} sx={{ height: 4 }} />;
      
      case 'paragraph':
        return (
          <ParagraphText key={index}>
            {Array.isArray(segment.content) 
              ? segment.content.map(renderTextSegment)
              : segment.content
            }
          </ParagraphText>
        );
      
      default:
        return renderTextSegment(segment, index);
    }
  };

  return (
    <FormattedText>
      {segments.map(renderSegment)}
    </FormattedText>
  );
};

/**
 * Normalizes URL for comparison to handle edge cases
 * @param {string} url - URL to normalize
 * @returns {string} Normalized URL
 */
const normalizeUrl = (url) => {
  if (!url) return '';
  
  let normalized = url.toLowerCase().trim();
  
  // Remove protocol differences
  normalized = normalized.replace(/^https?:\/\//, '');
  
  // Remove www prefix
  if (normalized.startsWith('www.')) {
    normalized = normalized.substring(4);
  }
  
  // Remove trailing slash
  if (normalized.endsWith('/')) {
    normalized = normalized.slice(0, -1);
  }
  
  // Remove fragment identifiers
  if (normalized.includes('#')) {
    normalized = normalized.split('#')[0];
  }
  
  return normalized;
};

/**
 * Removes duplicate references based on URL
 * @param {Array} references - Array of reference objects
 * @returns {Array} Deduplicated references
 */
const deduplicateReferences = (references) => {
  if (!references || !Array.isArray(references)) return [];
  
  const seen = new Set();
  const deduplicated = [];
  
  references.forEach((ref) => {
    const url = ref.url || ref.link || ref.source_url || ref.href || '';
    const normalizedUrl = normalizeUrl(url);
    
    if (normalizedUrl && !seen.has(normalizedUrl)) {
      seen.add(normalizedUrl);
      // Ensure sequential IDs for deduplicated references
      deduplicated.push({
        ...ref,
        id: deduplicated.length + 1
      });
    }
  });
  
  return deduplicated;
};

/**
 * Message bubble component that displays individual chat messages
 * @param {Object} message            - The message object
 * @param {string} message.type       - Type of message ('user' or 'assistant')
 * @param {string} message.content    - The text content of the message
 * @param {Array} message.references  - Optional array of reference objects for assistant messages
 * @param {Date} message.timestamp    - When the message was created
 * @returns {JSX.Element} The styled message bubble component
 */
const MessageBubble = forwardRef(({ message }, ref) => {
  const { type, content, references, timestamp } = message;

  // Deduplicate references on the frontend as a backup
  const uniqueReferences = deduplicateReferences(references);

  /**
   * Formats a Date object into a readable time string
   * @param {Date} date               - The date to format
   * @returns {string} Formatted time string (e.g., "2:30 PM")
   */
  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  /**
   * Handles clicking on a reference button to open the source URL
   * @param {Object} reference - The reference object containing the URL
   * @param {Event} event - The click event
   */
  const handleReferenceClick = (reference, event) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Get the URL path from the reference
    const urlPath = reference.url || reference.link || reference.source_url || reference.href;
    
    if (urlPath) {
      // Check if it's already a complete URL
      let fullUrl;
      if (urlPath.startsWith('http://') || urlPath.startsWith('https://')) {
        fullUrl = urlPath;
      } else {
        // Prepend the base domain to the URL path
        fullUrl = `https://www.madewithnestle.ca/${urlPath}`;
      }
      
      window.open(fullUrl, '_blank', 'noopener,noreferrer');
    } else {
      alert('Sorry, the source link is not available for this reference.');
    }
  };

  // Parse message content for formatting
  const contentSegments = parseMessageContent(content);

  return (
    <MessageContainer messagetype={type} ref={ref}>
      {/* Show avatar for assistant messages */}
      {type === 'assistant' && (
        <AssistantAvatar>
          <NestleAvatarLogo src={nestleLogoCircle} alt="Nestlé Logo" />
        </AssistantAvatar>
      )}
      
      <MessageContent>
        {/* Main message text */}
        <MessageText messagetype={type} elevation={0}>
          <FormattedMessageContent segments={contentSegments} references={uniqueReferences} />
        </MessageText>
        
        {/* References section - small buttons */}
        {uniqueReferences && uniqueReferences.length > 0 && (
          <ReferencesContainer>
            <ReferencesLabel>Sources:</ReferencesLabel>
            {uniqueReferences.map((ref, index) => (
              <StyledTooltip 
                key={index}
                title={formatReferenceTooltip(ref)}
                placement="top"
                arrow
                enterDelay={300}
                leaveDelay={100}
              >
                <Box
                  onClick={(event) => handleReferenceClick(ref, event)}
                  sx={{ display: 'inline-block', cursor: 'pointer' }}
                >
                  <ReferenceButton 
                    label={index + 1} 
                    size="small"
                    component="div"
                  />
                </Box>
              </StyledTooltip>
            ))}
          </ReferencesContainer>
        )}
        
        {/* Message timestamp */}
        <MessageTime messagetype={type}>
          {formatTime(timestamp)}
        </MessageTime>
      </MessageContent>
    </MessageContainer>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble; 