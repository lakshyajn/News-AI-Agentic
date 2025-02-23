import axios from "axios";

const API_URL = "http://127.0.0.1:8000"; // Make sure FastAPI is running here

export const fetchArticles = async () => {
  try {
    const response = await axios.get(`${API_URL}/articles/`);
    return response.data;
  } catch (error) {
    console.error("Axios error:", error);
    throw error;
  }
};