"use client";
import { useEffect, useState } from "react";
import axios from "axios";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState("english");

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
    const interval = setInterval(fetchNews, 30000);
    return () => clearInterval(interval);
  }, []);

  // ✅ Handle Language Change
  const handleLanguageChange = (selectedLang) => {
    setLanguage(selectedLang);
  };

  return (
    <div className="container mx-auto p-6">
      {/* ✅ Header */}
      <h1 className="text-4xl font-extrabold mb-6 text-center text-white">
        📰 AI-Generated News
      </h1>

      {/* ✅ Language Selection Buttons */}
      <div className="flex justify-center mb-6">
        <button
          onClick={() => handleLanguageChange("english")}
          className={`px-6 py-2 mx-2 rounded-lg text-lg font-semibold transition ${
            language === "english"
              ? "bg-blue-500 text-white shadow-lg"
              : "bg-gray-700 text-gray-300"
          }`}
        >
          English
        </button>
        <button
          onClick={() => handleLanguageChange("hindi")}
          className={`px-6 py-2 mx-2 rounded-lg text-lg font-semibold transition ${
            language === "hindi"
              ? "bg-green-500 text-white shadow-lg"
              : "bg-gray-700 text-gray-300"
          }`}
        >
          हिंदी
        </button>
      </div>

      {/* ✅ News Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          // ✅ Loading Skeleton
          [...Array(6)]?.map((_, index) => (
            <div key={index} className="bg-gray-800 p-6 rounded-lg animate-pulse">
              <div className="h-6 bg-gray-700 w-3/4 mb-4 rounded"></div>
              <div className="h-4 bg-gray-700 w-full mb-4 rounded"></div>
              <div className="h-64 bg-gray-700 w-full rounded"></div>
            </div>
          ))
        ) : articles?.length === 0 ? (
          <p className="text-center text-gray-400 text-lg">
            No news available at the moment.
          </p>
        ) : (
          articles.map((article, index) => (
            <div
              key={index}
              className="bg-gray-900 p-6 rounded-lg shadow-md hover:shadow-xl transition"
            >
              {/* ✅ News Title */}
              <h2 className="text-2xl font-bold text-white mb-2">
                {article.title}
              </h2>

              {/* ✅ News Summary (Dynamic Language) */}
              <p className="text-gray-400 mb-4">
                {language === "english"
                  ? article.summary
                  : article.summary_hindi}
              </p>

              {/* ✅ Display AI-Generated Image */}
              {article.image_url &&
              (article.image_url.startsWith("http") ||
                article.image_url.startsWith("data:image")) ? (
                <img
                  src={article.image_url}
                  alt="AI Generated"
                  className="mt-3 rounded-lg w-full h-64 object-cover"
                />
              ) : (
                <p className="text-red-500">Image not available</p>
              )}

              {/* ✅ Read More Button */}
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 block mt-4 font-semibold"
              >
                Read More →
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  );
}