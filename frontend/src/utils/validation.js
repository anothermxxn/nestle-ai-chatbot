/**
 * Validates Canadian FSA (Forward Sortation Area) format
 * @param {string} fsa - FSA to validate
 * @returns {boolean} True if valid FSA format
 */
export const validateFSA = (fsa) => {
  if (!fsa || typeof fsa !== 'string') return false;
  
  const cleanFSA = fsa.trim().replace(/\s/g, '').toUpperCase();
  
  // Canadian FSA format: Letter-Digit-Letter, excluding restricted letters
  const restrictedFirstLetters = ['D', 'F', 'I', 'O', 'Q', 'U'];
  
  return /^[A-Z][0-9][A-Z]$/.test(cleanFSA) && 
         !restrictedFirstLetters.includes(cleanFSA[0]);
};

/**
 * Gets validation message for FSA input
 * @param {string} inputValue - The input value to validate
 * @returns {string} Validation message or empty string if valid
 */
export const getFSAValidationMessage = (inputValue) => {
  if (!inputValue || inputValue.length === 0) return '';
  
  const cleanInput = inputValue.trim().toUpperCase();
  
  if (cleanInput.length < 3) {
    return 'Enter 3 characters (e.g., K1A)';
  }

  const firstLetter = cleanInput[0];
  const restrictedFirstLetters = ['D', 'F', 'I', 'O', 'Q', 'U'];
  
  if (!/^[A-Z][0-9][A-Z]$/.test(cleanInput) || restrictedFirstLetters.includes(firstLetter)) {
    return 'Please enter a valid Canadian postal code (e.g., K1A)';
  }
  
  return '';
};

/**
 * Cleans and formats FSA input
 * @param {string} input - Raw FSA input
 * @returns {string} Cleaned and formatted FSA
 */
export const formatFSA = (input) => {
  if (!input || typeof input !== 'string') return '';
  
  return input.trim().replace(/\s/g, '').toUpperCase().substring(0, 3);
};

export default {
  validateFSA,
  getFSAValidationMessage,
  formatFSA,
}; 