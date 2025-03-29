import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage, fetchConversationHistory } from "../api/api";
import { marked } from "marked";

// SVG Icons
const UserIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="white">
    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
  </svg>
);

const AIIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">
  <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
  <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
  <g id="SVGRepo_iconCarrier">
    <rect x="10" y="12" width="28" height="20" rx="5" ry="5" stroke="black" stroke-width="2" fill="white"/>
    <circle cx="18" cy="20" r="3" fill="black"/>
    <circle cx="30" cy="20" r="3" fill="black"/>
    <rect x="15" y="26" width="18" height="2" fill="black"/>
    <rect x="6" y="18" width="4" height="12" rx="2" ry="2" fill="white" stroke="black" stroke-width="2"/>
    <rect x="38" y="18" width="4" height="12" rx="2" ry="2" fill="white" stroke="black" stroke-width="2"/>
    <line x1="24" y1="4" x2="24" y2="10" stroke="black" stroke-width="2"/>
    <circle cx="24" cy="4" r="2" fill="black"/>
    <rect x="14" y="32" width="20" height="10" rx="3" ry="3" stroke="black" stroke-width="2" fill="white"/>
  </g>
</svg>

);

function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load conversation history on component mount
  useEffect(() => {
    const loadConversationHistory = async () => {
      try {
        setIsLoading(true);
        const history = await fetchConversationHistory();
        
        if (history && history.length > 0) {
          console.log("Loaded conversation history:", history);
          // If we have history, use it
          setMessages(history);
        } else {
          // If no history, add default welcome message to UI and save to database
          const welcomeMessage = {
            role: "assistant",
            content: "Hi, how can I help you today?"
          };
          setMessages([welcomeMessage]);
          
        }
      } catch (error) {
        console.error("Error loading conversation history:", error);
        // Set default message on error
        setMessages([{
          role: "assistant",
          content: "Hi, how can I help you today?"
        }]);
      } finally {
        setIsLoading(false);
        setHistoryLoaded(true);
      }
    };

    loadConversationHistory();
  }, []);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (userInput) => {
    if (userInput.trim() === "" || isLoading) return;
    
    try {
      // Add user message to UI immediately
      setMessages(prevMessages => [...prevMessages, { role: "user", content: userInput }]);
      setInput("");
      setIsLoading(true);

      // Show typing indicator
      setMessages(prevMessages => [...prevMessages, { role: "assistant", content: "...", isTyping: true }]);
      
      // Call API to get AI response
      const aiResponse = await getAIMessage(userInput);
      
      // Remove typing indicator and add real response
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => !msg.isTyping);
        return [...filtered, aiResponse];
      });
    } catch (error) {
      console.error("Error sending message:", error);
      // Remove typing indicator and add error message
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => !msg.isTyping);
        return [...filtered, { 
          role: "assistant", 
          content: "Sorry, I encountered an error processing your request. Please try again later." 
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSend(input);
      e.preventDefault();
    }
  };

  // Show loading spinner before history is loaded
  if (!historyLoaded) {
    return (
      <div className="messages-container">
        <div className="loading-spinner">Loading conversation...</div>
      </div>
    );
  }

  return (
    <>
      <div className="header">
        <div className="header-left">
          <img 
            src="https://partselectcom-gtcdcddbene3cpes.z01.azurefd.net/images/ps-25-year-logo.svg" 
            alt="PartSelect Logo" 
            className="header-logo" 
          />
          <h2>Chat Assistant</h2>
        </div>
        <div className="header-right">
          <img 
            src="https://instalily.ai/_next/image?url=%2Flogo.png&w=128&q=75" 
            alt="Instalily Logo" 
            className="header-logo-right" 
          />
        </div>
      </div>
      <div className="messages-container">
        {messages.map((message, index) => (
        <div key={index} className={`${message.role}-message-container`}>
          {/* Add avatar for the message */}
          <div className={`avatar ${message.role}-avatar`}>
            {message.role === "user" ? <UserIcon /> : <AIIcon />}
          </div>
          
          {message.isTyping ? (
            <div className={`message ${message.role}-message typing`}>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          ) : (
            <div className={`message ${message.role}-message`}>
              <div dangerouslySetInnerHTML={{
                __html: marked(message.content).replace(/<p>|<\/p>/g, "")
              }}></div>
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
        <button 
          className={isLoading ? 'disabled' : ''}
          onClick={() => handleSend(input)}
          disabled={isLoading}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
    </>
  );
}

export default ChatWindow;