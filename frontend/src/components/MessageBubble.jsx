import { Box, Typography, Paper, Chip, Tooltip, Link } from '@mui/material';
import { styled } from '@mui/material/styles';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import { colors, fontFamily, StyledAvatar } from './common';
import { parseMessageContent, formatReferenceTooltip } from '../utils/messageFormatter';

// Styled components
const MessageContainer = styled(Box)(({ messagetype }) => ({
  display: 'flex',
  margin: '12px 0',
  maxWidth: '95%',
  fontFamily,
  fontWeight: 600,
  justifyContent: messagetype === 'user' ? 'flex-end' : 'flex-start',
  alignItems: messagetype === 'user' ? 'center' : 'flex-start',
  gap: messagetype === 'user' ? 0 : 8,
  position: messagetype === 'user' ? 'static' : 'relative',
  marginLeft: messagetype === 'user' ? 'auto' : 0,
}));

const AssistantAvatar = styled(StyledAvatar)({
  position: 'absolute',
  top: 0,
  left: 0,
  zIndex: 1,
  '& .MuiSvgIcon-root': {
    fontSize: 28,
    margin: '4px',
  },
});

const MessageContent = styled(Box)(({ messagetype }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  marginLeft: messagetype === 'assistant' ? 44 : 0,
}));

const MessageText = styled(Paper)(({ messagetype }) => ({
  padding: '8px 12px',
  borderRadius: 8,
  fontSize: 14,
  lineHeight: 1.4,
  wordWrap: 'break-word',
  fontWeight: 500,
  background: messagetype === 'user' 
    ? colors.gray100 
    : messagetype === 'system' 
    ? colors.gray200 
    : colors.primary,
  color: messagetype === 'user' 
    ? colors.primary 
    : messagetype === 'system' 
    ? colors.gray600 
    : colors.white,
  borderBottomRightRadius: messagetype === 'user' ? 4 : 8,
  borderBottomLeftRadius: messagetype === 'assistant' ? 4 : 8,
  boxShadow: 'none',
  ...(messagetype === 'system' && {
    textAlign: 'center',
    fontStyle: 'italic',
    fontSize: 12,
    margin: '4px auto',
    maxWidth: '200px',
  }),
}));

const FormattedText = styled(Box)({
  fontSize: 14,
  lineHeight: 1.5,
});

const BoldText = styled('span')({
  fontWeight: "bold",
});

const UnderlinedText = styled('span')({
  textDecoration: 'underline',
});

const BoldUnderlinedText = styled('span')({
  fontWeight: "bold",
  textDecoration: 'underline',
});

const BulletList = styled(Box)({
  marginLeft: 16,
  marginTop: 2,
  marginBottom: 2,
});

const BulletItem = styled(Box)({
  display: 'flex',
  alignItems: 'flex-start',
  marginBottom: 1,
  '&::before': {
    content: '"•"',
    color: colors.white,
    fontWeight: 'bold',
    width: 12,
    marginRight: 8,
    marginTop: 1,
    flexShrink: 0,
  },
});

const NumberedList = styled(Box)({
  marginLeft: 16,
  marginTop: 2,
  marginBottom: 2,
});

const NumberedItem = styled(Box)(({ number }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  marginBottom: 2,
  '&::before': {
    content: `"${number}."`,
    color: colors.white,
    fontWeight: 'bold',
    minWidth: 24,
    marginRight: 8,
    marginTop: 1,
    flexShrink: 0,
  },
}));

const StyledLink = styled(Link)({
  color: colors.white,
  textDecoration: 'underline',
  cursor: 'pointer',
  '&:hover': {
    color: colors.gray100,
    textDecoration: 'underline',
  },
});

const ParagraphText = styled(Box)({
  marginBottom: 4,
  '&:last-child': {
    marginBottom: 0,
  },
});

const ReferencesContainer = styled(Box)({
  display: 'flex',
  flexWrap: 'wrap',
  gap: 4,
  marginTop: 8,
  alignItems: 'center',
});

const ReferencesLabel = styled(Typography)({
  fontSize: 11,
  fontWeight: 600,
  color: colors.gray500,
  marginRight: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
});

const ReferenceButton = styled(Chip)({
  background: colors.gray400,
  color: colors.white,
  width: 20,
  height: 20,
  fontSize: 10,
  fontWeight: 'bold',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  '& .MuiChip-label': {
    padding: 0,
  },
  '&:hover': {
    background: colors.primary,
    transform: 'scale(1.15)',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
  },
  '&:active': {
    transform: 'scale(1.05)',
  },
});

const StyledTooltip = styled(({ className, ...props }) => (
  <Tooltip {...props} classes={{ popper: className }} />
))({
  '& .MuiTooltip-tooltip': {
    backgroundColor: colors.gray800,
    color: colors.white,
    fontSize: 12,
    fontWeight: 500,
    fontFamily,
    padding: '8px 12px',
    borderRadius: 6,
    maxWidth: 250,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    border: `1px solid ${colors.gray600}`,
  },
  '& .MuiTooltip-arrow': {
    color: colors.gray800,
    '&::before': {
      border: `1px solid ${colors.gray600}`,
    },
  },
});

const MessageTime = styled(Typography)(({ messagetype }) => ({
  fontSize: 11,
  color: colors.gray500,
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
const MessageBubble = ({ message }) => {
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
    <MessageContainer messagetype={type}>
      {/* Show avatar for assistant messages */}
      {type === 'assistant' && (
        <AssistantAvatar size="large">
          <SmartToyOutlinedIcon />
        </AssistantAvatar>
      )}
      
      <MessageContent messagetype={type}>
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
};

export default MessageBubble; 