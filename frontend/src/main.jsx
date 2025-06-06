import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/global.css'
import App from './App.jsx'

const setViewportHeight = () => {
  const vh = window.innerHeight * 0.01;
  document.documentElement.style.setProperty('--vh', `${vh}px`);
};

// Orientation detection and locking
const handleOrientationChange = () => {
  setTimeout(setViewportHeight, 100);
};

// Set initial viewport height
setViewportHeight();

// Handle viewport height changes
window.addEventListener('resize', setViewportHeight);
window.addEventListener('orientationchange', handleOrientationChange);

// Handle window blur/focus for PWA-like behavior
window.addEventListener('blur', () => {
  document.title = 'Smartie - Nestle AI Chatbot';
});

window.addEventListener('focus', () => {
  document.title = 'Smartie - Nestle AI Chatbot';
});

// Prevent zoom on double tap for iOS
let lastTouchEnd = 0;
document.addEventListener('touchend', (event) => {
  const now = (new Date()).getTime();
  if (now - lastTouchEnd <= 300) {
    event.preventDefault();
  }
  lastTouchEnd = now;
}, false);

// Disable pull-to-refresh on mobile
document.addEventListener('touchstart', (event) => {
  if (event.touches.length > 1) {
    event.preventDefault();
  }
}, { passive: false });

let lastTouchY = 0;
document.addEventListener('touchmove', (event) => {
  const touchY = event.touches[0].clientY;
  const touchYDelta = touchY - lastTouchY;
  lastTouchY = touchY;

  if (touchYDelta > 0 && window.scrollY === 0) {
    event.preventDefault();
  }
}, { passive: false });

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
