import { v4 as uuidv4 } from 'uuid';

// Configuration constants
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;
const API_BEARER_TOKEN = process.env.REACT_APP_API_BEARER_TOKEN || '';

// Session management
const getSessionId = async () => {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('session_id', sessionId);
    await saveWelcomeMessage(sessionId); // Ensure saveWelcomeMessage is an async function
  }
  return sessionId;
};

// Get user ID from local storage or generate new one
const getUserId = () => {
  let userId = localStorage.getItem('user_id');
  if (!userId) {
    userId = uuidv4();
    localStorage.setItem('user_id', userId);
  }
  return userId;
};

/**
 * Save welcome message for new sessions
 * @returns {Promise<Object>} - Status of the operation
 */
export const saveWelcomeMessage = async (sessionId) => {
  try {
    const userId = getUserId();
    const requestId = uuidv4();
    
    const response = await fetch(`${API_BASE_URL}/api/save-welcome-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_BEARER_TOKEN}`
      },
      body: JSON.stringify({
        user_id: userId,
        request_id: requestId,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to save welcome message');
    }
    
    return { success: true };
  } catch (error) {
    console.error('Error saving welcome message:', error);
    return { success: false };
  }
};

/**
 * Get AI message by calling the parts-select-ai-expert endpoint
 * @param {string} query - User's input message
 * @returns {Promise<Object>} - AI response message object
 */
export const getAIMessage = async (query) => {
  try {
    const sessionId = await getSessionId();
    const userId = getUserId();
    const requestId = uuidv4();
    
    const requestData = {
      query,
      user_id: userId,
      request_id: requestId,
      session_id: sessionId
    };

    const response = await fetch(`${API_BASE_URL}/api/parts-select-ai-expert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_BEARER_TOKEN}`
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get AI response');
    }

    const data = await response.json();
    
    // Return the AI response from the data
    return {
      role: 'assistant',
      content: (data && data.ai_content) ? data.ai_content : 'I processed your request successfully.'
    };
  } catch (error) {
    console.error('Error getting AI message:', error);
    return {
      role: 'assistant',
      content: 'Sorry, I encountered an error processing your request. Please try again later.'
    };
  }
};

/**
 * Fetch the most recent message for the current session
 * @param {string} sessionId - Current session ID
 * @returns {Promise<Object>} - Latest message object
 */
const fetchLatestMessage = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messages/latest?session_id=${sessionId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_BEARER_TOKEN}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch latest message');
    }

    const data = await response.json();
    
    if (data && data.message) {
      return {
        role: data.message.type === 'human' ? 'user' : 'assistant',
        content: data.message.content
      };
    }
    
    return null;
  } catch (error) {
    console.error('Error fetching latest message:', error);
    return null;
  }
};

/**
 * Fetch conversation history for the current session
 * @param {number} limit - Maximum number of messages to fetch
 * @returns {Promise<Array>} - Array of message objects
 */
export const fetchConversationHistory = async (limit = 20) => {
  try {
    const sessionId = await getSessionId();
    
    const response = await fetch(`${API_BASE_URL}/api/messages?session_id=${sessionId}&limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_BEARER_TOKEN}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch conversation history');
    }

    const data = await response.json();
    
    if (data && Array.isArray(data)) {
      // Sort messages by timestamp to ensure correct order
      const sortedData = [...data].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
      });
      
      return sortedData.map(item => ({
        role: item.message.type === 'human' ? 'user' : 'assistant',
        content: item.message.content
      }));
    }
    
    return [];
  } catch (error) {
    console.error('Error fetching conversation history:', error);
    return [];
  }
};