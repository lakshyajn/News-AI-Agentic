"use client"
import { useEffect, useState } from "react";
import axios from "axios";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState("english"); // ✅ Default Language: English

  // ✅ Fetch news automatically when the page loads
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/articles/");
        setArticles(response.data.articles);
      } catch (error) {
        console.error("Error fetching news:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchNews();
    const interval = setInterval(fetchNews, 30000); // ✅ Refresh news every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // ✅ Handle Language Change
  const handleLanguageChange = (selectedLang) => {
    setLanguage(selectedLang);
  };

  if (loading) return <p className="text-center text-gray-400">Loading news...</p>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4 text-center">Latest AI-Generated News</h1>
      
      {/* ✅ Language Selection Dropdown */}
      <div className="flex justify-center mb-4">
        <button 
          onClick={() => handleLanguageChange("english")}
          className={`px-4 py-2 mx-2 rounded-md ${
            language === "english" ? "bg-blue-500 text-white" : "bg-gray-300 text-black"
          }`}
        >
          English
        </button>
        <button 
          onClick={() => handleLanguageChange("hindi")}
          className={`px-4 py-2 mx-2 rounded-md ${
            language === "hindi" ? "bg-green-500 text-white" : "bg-gray-300 text-black"
          }`}
        >
          हिंदी
        </button>
      </div>

      {/* ✅ News Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {articles.length === 0 ? (
          <p className="text-center text-gray-500">No news available.</p>
        ) : (
          articles.map((article, index) => (
            <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-xl font-bold">{article.title}</h2>
              <p className="text-gray-400">
                {language === "english" ? article.summary : article.summary_hindi}
              </p>
              
              {/* ✅ Fix Image Issue - Ensure Image URL is Valid */}
              {article.image_url && article.image_url.startsWith("http") ? (
                <img 
                  src={article.image_url} 
                  alt="AI Generated" 
                  className="mt-3 rounded-lg w-full h-auto"
                />
              ) : (
                <p className="text-red-500">Image not available</p>
              )}

              <a href={article.url} target="_blank" className="text-blue-500 block mt-2">Read More →</a>
            </div>
          ))
        )}
      </div>
    </div>
  );
}