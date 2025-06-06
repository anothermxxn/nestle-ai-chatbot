/**
 * Groups consecutive bullet points and numbered items for better visual presentation
 * Also handles nested structures (numbered items with bullet sub-items)
 * @param {Array} segments - Array of parsed segments
 * @returns {Array} Array with grouped list items
 */
const groupListItems = (segments) => {
  const grouped = [];
  let i = 0;
  
  while (i < segments.length) {
    const segment = segments[i];
    
    if (segment.type === 'numbered') {
      // Start a new numbered group
      const numberedGroup = {
        type: 'numbered_group',
        items: [segment]
      };
      
      // Look ahead for bullet points that should be grouped with this numbered item
      let j = i + 1;
      const associatedBullets = [];
      
      // Skip line breaks and collect bullets until we hit another numbered item or different content
      while (j < segments.length) {
        const nextSegment = segments[j];
        
        if (nextSegment.type === 'linebreak') {
          j++;
          continue;
        }
        
        if (nextSegment.type === 'bullet') {
          associatedBullets.push(nextSegment);
          j++;
        } else {
          // Hit something else, stop collecting bullets
          break;
        }
      }
      
      // If we found bullets, create a nested structure
      if (associatedBullets.length > 0) {
        numberedGroup.items[0].subItems = associatedBullets;
        i = j; // Skip past all the bullets we consumed
      } else {
        i++;
      }
      
      grouped.push(numberedGroup);
      
    } else if (segment.type === 'bullet') {
      // Handle standalone bullet groups (not associated with numbered items)
      const bulletGroup = {
        type: 'bullet_group',
        items: [segment]
      };
      
      // Collect consecutive bullets
      let j = i + 1;
      while (j < segments.length && segments[j].type === 'bullet') {
        bulletGroup.items.push(segments[j]);
        j++;
      }
      
      grouped.push(bulletGroup);
      i = j;
      
    } else {
      // Regular segment, add as-is
      grouped.push(segment);
      i++;
    }
  }
  
  return grouped;
};

/**
 * Parses message content and converts markdown-like formatting to structured segments
 * Supports: **bold**, __underlined__, bullet points, numbered lists, headers, line breaks, and links
 * @param {string} content - The raw message content
 * @returns {Array} Array of text segments with formatting information
 */
export const parseMessageContent = (content) => {
  if (!content) return [];

  const segments = [];
  const lines = content.split('\n');
  let consecutiveEmptyLines = 0;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Handle empty lines more carefully
    if (line.trim() === '') {
      consecutiveEmptyLines++;
      // Only add one line break for multiple consecutive empty lines
      if (consecutiveEmptyLines === 1 && segments.length > 0) {
        segments.push({
          type: 'linebreak',
          content: '\n'
        });
      }
      continue;
    }
    
    consecutiveEmptyLines = 0;
    
    // Check for horizontal rules (--- or ——— or similar)
    if (line.trim().match(/^[-—–]{3,}$/)) {
      segments.push({
        type: 'linebreak',
        content: '\n'
      });
      continue;
    }
    
    // Check for headers (## Header or ### Header)
    const headerMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      segments.push({
        type: 'header',
        level: level,
        content: headerMatch[2].trim()
      });
      continue;
    }
    
    // Check for numbered lists with enhanced pattern matching
    // Matches: "1. **Title:**" or "1. **Title**" or "1. Title:" or "1. Title"
    const numberedMatch = line.match(/^[\s]*(\d+)[.)]\s+(.+)$/);
    if (numberedMatch) {
      const numberedContent = parseBoldAndLinks(numberedMatch[2]);
      segments.push({
        type: 'numbered',
        number: parseInt(numberedMatch[1]),
        content: numberedContent
      });
      continue;
    }
    
    // Check for bullet points with enhanced indentation detection
    // Matches: "- item", "* item", "  - item", "   • item"
    const bulletMatch = line.match(/^[\s]*[-*•]\s+(.+)$/);
    if (bulletMatch) {
      const bulletContent = parseBoldAndLinks(bulletMatch[1]);
      const indentLevel = line.search(/[-*•]/);
      segments.push({
        type: 'bullet',
        content: bulletContent,
        indentLevel: indentLevel
      });
      continue;
    }
    
    // Regular text line - parse for bold and links
    const textContent = parseBoldAndLinks(line);
    if (textContent.length > 0) {
      segments.push({
        type: 'paragraph',
        content: textContent
      });
    }
  }
  
  // Group consecutive items for better presentation
  return groupListItems(segments);
};

/**
 * Parses a text string for bold formatting, underlined formatting, and links
 * Supports nested formatting like **__bold and underlined__**
 * @param {string} text - The text to parse
 * @returns {Array} Array of text segments with bold, underline, and link formatting
 */
const parseBoldAndLinks = (text) => {
  if (!text) return [];

  // Process text in multiple passes to handle nested formatting
  return parseFormattingRecursive(text);
};

/**
 * Recursively parses text for formatting, handling nested cases
 * @param {string} text - The text to parse
 * @param {Array} appliedFormats - Currently applied formatting types
 * @returns {Array} Array of text segments
 */
const parseFormattingRecursive = (text, appliedFormats = []) => {
  if (!text) return [];
  
  // Order matters: process in order of precedence
  const formatPatterns = [
    { regex: /(\[([^\]]+)\]\(([^)]+)\))/g, type: 'link' },      // Links first
    { regex: /(https?:\/\/[^\s]+)/g, type: 'url' },             // Plain URLs
    { regex: /(\*\*(.*?)\*\*)/g, type: 'bold' },                // Bold
    { regex: /(__(.+?)__)/g, type: 'underline' }                // Underline
  ];

  let foundMatch = false;
  
  for (const pattern of formatPatterns) {
    const regex = new RegExp(pattern.regex.source, 'g');
    let match;
    let lastIndex = 0;
    const currentSegments = [];
    
    while ((match = regex.exec(text)) !== null) {
      foundMatch = true;
      
      // Add text before the match
      if (match.index > lastIndex) {
        const beforeText = text.slice(lastIndex, match.index);
        if (beforeText) {
          currentSegments.push(...parseFormattingRecursive(beforeText, appliedFormats));
        }
      }

      // Handle the matched formatting
      if (pattern.type === 'link') {
        currentSegments.push({
          type: 'link',
          content: match[2],
          url: match[3],
          appliedFormats: [...appliedFormats]
        });
      } else if (pattern.type === 'url') {
        currentSegments.push({
          type: 'link',
          content: match[1],
          url: match[1],
          appliedFormats: [...appliedFormats]
        });
      } else if (pattern.type === 'bold') {
        const innerContent = match[2];
        const newFormats = [...appliedFormats, 'bold'];
        
        // Recursively parse the inner content for nested formatting
        const innerSegments = parseFormattingRecursive(innerContent, newFormats);
        
        if (innerSegments.length === 1 && innerSegments[0].type === 'text') {
          // Simple case: just bold text
          currentSegments.push({
            type: 'bold',
            content: innerContent,
            appliedFormats: newFormats
          });
        } else {
          // Complex case: nested formatting
          currentSegments.push(...innerSegments);
        }
      } else if (pattern.type === 'underline') {
        const innerContent = match[2];
        const newFormats = [...appliedFormats, 'underline'];
        
        // Recursively parse the inner content for nested formatting
        const innerSegments = parseFormattingRecursive(innerContent, newFormats);
        
        if (innerSegments.length === 1 && innerSegments[0].type === 'text') {
          // Simple case: just underlined text
          currentSegments.push({
            type: 'underline',
            content: innerContent,
            appliedFormats: newFormats
          });
        } else {
          // Complex case: nested formatting
          currentSegments.push(...innerSegments);
        }
      }

      lastIndex = regex.lastIndex;
    }

    // If we found matches for this pattern, process the remaining text and return
    if (foundMatch) {
      // Add remaining text after the last match
      if (lastIndex < text.length) {
        const remainingText = text.slice(lastIndex);
        if (remainingText) {
          currentSegments.push(...parseFormattingRecursive(remainingText, appliedFormats));
        }
      }
      
      return currentSegments;
    }
  }

  // No formatting found, return as text with applied formats
  if (appliedFormats.length > 0) {
    return [{
      type: appliedFormats[appliedFormats.length - 1], // Use the most recent format
      content: text,
      appliedFormats: appliedFormats
    }];
  } else {
    return [{
      type: 'text',
      content: text,
      appliedFormats: []
    }];
  }
};

/**
 * Extracts reference numbers from text content (e.g., [1], [2])
 * @param {string} content - The message content
 * @returns {Array} Array of reference numbers found in the text
 */
export const extractReferenceNumbers = (content) => {
  if (!content) return [];

  const regex = /\[(\d+)\]/g;
  const references = [];
  let match;

  while ((match = regex.exec(content)) !== null) {
    references.push(parseInt(match[1], 10));
  }

  return references;
};

/**
 * Cleans and formats a title string for display
 * @param {string} title - The raw title string
 * @returns {string} Cleaned and formatted title
 */
const cleanTitle = (title) => {
  if (!title || typeof title !== 'string') return '';

  // Remove URLs if the title is just a URL
  if (title.startsWith('http://') || title.startsWith('https://')) {
    // Extract meaningful part from URL
    try {
      const url = new URL(title);
      const pathname = url.pathname;
      
      // Get the last meaningful segment
      const segments = pathname.split('/').filter(segment => segment && segment !== 'recipes');
      if (segments.length > 0) {
        const lastSegment = segments[segments.length - 1];
        // Convert URL-style names to readable format
        return lastSegment
          .replace(/-/g, ' ')
          .replace(/_/g, ' ')
          .split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ');
      }
    } catch {
      // If URL parsing fails, try to extract domain
      const domainMatch = title.match(/https?:\/\/(?:www\.)?([^/]+)/);
      if (domainMatch && domainMatch[1]) {
        return domainMatch[1].replace(/\./g, ' ').toUpperCase();
      }
    }
  }

  // Clean up common unwanted patterns
  let cleaned = title
    .replace(/^https?:\/\/[^\s]+/g, '') // Remove URLs at the start
    .replace(/\([^)]*\)/g, '') // Remove content in parentheses
    .replace(/\[[^\]]*\]/g, '') // Remove content in brackets
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();

  // If title is too long, truncate it intelligently
  if (cleaned.length > 60) {
    const words = cleaned.split(' ');
    if (words.length > 8) {
      cleaned = words.slice(0, 8).join(' ') + '...';
    } else {
      cleaned = cleaned.substring(0, 57) + '...';
    }
  }

  return cleaned || 'Untitled';
};

/**
 * Formats a reference title for display in tooltip
 * @param {Object} reference - The reference object
 * @returns {string} Formatted title for tooltip
 */
export const formatReferenceTooltip = (reference) => {
  if (!reference) return 'Reference';

  // Try different title fields in order of preference
  const rawTitle = reference.title || reference.page_title || reference.section_title || '';
  const rawSection = reference.section_title || reference.section || '';
  
  // Clean the main title
  const cleanedTitle = cleanTitle(rawTitle);
  const cleanedSection = cleanTitle(rawSection);
  
  // Don't show "Untitled" in tooltips - just use the main title
  if (cleanedSection === 'Untitled' || !cleanedSection) {
    return cleanedTitle || 'Reference';
  }
  
  // If we have both title and section, and they're different
  if (cleanedTitle && cleanedSection && cleanedTitle !== cleanedSection) {
    // Avoid redundancy - if section is contained in title, just use title
    if (cleanedTitle.toLowerCase().includes(cleanedSection.toLowerCase()) || 
        cleanedSection.toLowerCase().includes(cleanedTitle.toLowerCase())) {
      return cleanedTitle;
    }
    return `${cleanedTitle} - ${cleanedSection}`;
  }
  
  // Return the best available title
  return cleanedTitle || cleanedSection || 'Reference';
}; 