import { Box, Typography, Paper, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import { colors, fontFamily, shadows, StyledAvatar } from './common';

// Styled components
const MessageContainer = styled(Box)(({ messagetype }) => ({
  display: 'flex',
  margin: '12px 0',
  maxWidth: '85%',
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
  background: messagetype === 'user' ? colors.gray100 : colors.primary,
  color: messagetype === 'user' ? colors.primary : colors.white,
  borderBottomRightRadius: messagetype === 'user' ? 4 : 8,
  borderBottomLeftRadius: messagetype === 'assistant' ? 4 : 8,
  boxShadow: 'none',
}));

const ReferencesSection = styled(Paper)({
  background: colors.white,
  border: `1px solid ${colors.gray200}`,
  borderRadius: 6,
  padding: 12,
  marginTop: 8,
  boxShadow: shadows.light,
});

const ReferencesTitle = styled(Typography)({
  fontWeight: 700,
  fontSize: 12,
  color: colors.gray500,
  marginBottom: 8,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
});

const ReferencesList = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  gap: 6,
});

const ReferenceItem = styled(Box)({
  display: 'flex',
  alignItems: 'flex-start',
  gap: 8,
  fontSize: 12,
  lineHeight: 1.3,
  fontWeight: 500,
});

const ReferenceNumber = styled(Chip)({
  background: colors.primary,
  color: colors.white,
  width: 18,
  height: 18,
  fontSize: 10,
  fontWeight: 'bold',
  '& .MuiChip-label': {
    padding: 0,
  },
});

const ReferenceText = styled(Typography)({
  color: colors.gray600,
  flex: 1,
  fontSize: 12,
  lineHeight: 1.3,
});

const MessageTime = styled(Typography)(({ messagetype }) => ({
  fontSize: 11,
  color: colors.gray500,
  marginTop: 4,
  textAlign: messagetype === 'user' ? 'right' : 'left',
  fontWeight: 500,
}));

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
          <Typography variant="body2" sx={{ fontSize: 14, lineHeight: 1.5, fontWeight: 500 }}>
            {content}
          </Typography>
        </MessageText>
        
        {/* References section */}
        {references && references.length > 0 && (
          <ReferencesSection elevation={1}>
            <ReferencesTitle>References</ReferencesTitle>
            <ReferencesList>
              {references.map((ref, index) => (
                <ReferenceItem key={index}>
                  <ReferenceNumber 
                    label={index + 1} 
                    size="small"
                  />
                  <ReferenceText>
                    {ref.title || ref.content}
                  </ReferenceText>
                </ReferenceItem>
              ))}
            </ReferencesList>
          </ReferencesSection>
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