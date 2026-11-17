import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const sendMessage = async (message, userId, sessionId) => {
  const response = await axios.post(`${API_BASE}/chat/`, {
    message,
    user_id: userId,
    session_id: sessionId
  });
  return response.data;
};

export const getMood = async (userId) => {
  const response = await axios.get(`${API_BASE}/mood/${userId}`);
  return response.data;
};

export const searchMemories = async (query, userId) => {
  const response = await axios.post(`${API_BASE}/memories/search`, {
    query,
    user_id: userId,
    limit: 5
  });
  return response.data;
};
