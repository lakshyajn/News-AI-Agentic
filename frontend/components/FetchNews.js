"use client"
import React, { useState } from "react";
import axios from "axios";
import { toast } from "react-toastify";

export default function FetchNews() {
  const [url, setUrl] = useState("");

  const fetchNews = async () => {
    if (!url.trim()) {
      toast.error("Please enter a valid URL!");
      return;
    }

    try {
      const res = await axios.post("http://localhost:8000/fetch/", { url });
      toast.success("News article saved!");
      setUrl("");
    } catch (error) {
      toast.error("Failed to fetch news!");
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Enter news article URL"
        className="w-full p-2 rounded bg-gray-700 text-white"
      />
      <button
        onClick={fetchNews}
        className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
      >
        Fetch News
      </button>
    </div>
  );
}
