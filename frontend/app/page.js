"use client"
import { useEffect, useState } from "react";
import axios from "axios";
import NewsList from "@/components/NewsList";

export default function Home() {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8000/articles/")
      .then(res => setArticles(res.data.articles))
      .catch(err => console.error("Error fetching articles:", err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-6">📰 AI News</h1>
        <NewsList articles={articles} />
      </div>
    </div>
  );
}
