export default function NewsList({ articles }) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {articles.map((article, index) => (
          <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <img src={article.image_url} className="w-full h-40 object-cover rounded" />
            <h2 className="text-xl font-bold">{article.title}</h2>
            <p className="text-gray-400">{article.summary}</p>
            <a href={article.url} target="_blank" className="text-blue-500">
              Read More →
            </a>
          </div>
        ))}
      </div>
    );
  }  