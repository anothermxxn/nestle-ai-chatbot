import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const setViewportHeight = () => {
  const vh = window.innerHeight * 0.01;
  document.documentElement.style.setProperty('--vh', `${vh}px`);
};

// Orientation detection and locking
const handleOrientationChange = () => {
  setViewportHeight();
  
  if (screen.orientation && screen.orientation.lock) {
    try {
      screen.orientation.lock('portrait')
    } catch {
      // Silently fail if screen.orientation.lock is not supported
    }
  }
};

// Set initial viewport height
setViewportHeight();

// Update viewport height on resize and orientation change
window.addEventListener('resize', setViewportHeight);
window.addEventListener('orientationchange', () => {
  setTimeout(handleOrientationChange, 100);
});

// Try to lock orientation on initial load
handleOrientationChange();

// Additional orientation monitoring for modern browsers
if (screen.orientation) {
  screen.orientation.addEventListener('change', handleOrientationChange);
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
