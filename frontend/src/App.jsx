import ChatBot from './components/chat/ChatBot';
import './styles/app.css';

/**
 * Main application component that renders the chat interface
 * @returns {JSX.Element} The main app component with background and chatbot
 */
function App() {
  return (
    <div className="app">
      {/* Background container - placeholder for future background content */}
      <div className="blank-background">
        {/* Future: Background images, branding, or other content will be added here */}
      </div>

      {/* Main chat interface component */}
      <ChatBot />
    </div>
  );
}

export default App;
