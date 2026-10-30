import json
import re
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
ARTICLES_FILE = Path(__file__).resolve().parent / "articles.json"


def load_articles():
    if not ARTICLES_FILE.exists():
        return []
    with ARTICLES_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def search_articles(query, articles):
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    words = {word for word in words if len(word) > 2}
    broad_question = any(
        word in words
        for word in {"overall", "across", "themes", "compare", "summarize", "all"}
    )

    matches = []
    for article in articles:
        title = article.get("title", "")
        text = article.get("text", "")
        title_lower = title.lower()
        text_lower = text.lower()
        score = sum(
            4 * title_lower.count(word) + text_lower.count(word) for word in words
        )
        if score:
            matches.append((score, article))

    matches.sort(key=lambda item: item[0], reverse=True)
    if broad_question or not matches:
        chosen_articles = articles[:5]
    else:
        chosen_articles = [article for score, article in matches[:5]]

    return [
        {
            "title": article.get("title", "Untitled"),
            "url": article.get("url", ""),
            "text": article.get("text", ""),
        }
        for article in chosen_articles
    ]


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "No question provided"}), 400

    articles = load_articles()
    if not articles:
        return jsonify(
            {"answer": "articles.json is missing. Please run main.py first."}
        )

    results = search_articles(question, articles)

    if not results:
        answer = "I couldn't find any matching Resparkit articles for your question."
    else:
        response_lines = ["Here is what I found in the Resparkit articles:\n"]
        for res in results:
            title = res["title"]
            url = res["url"]
            snippet = (
                res["text"][:300] + "..." if len(res["text"]) > 300 else res["text"]
            )
            response_lines.append(f"**[{title}]({url})**\n{snippet}\n")

        answer = "\n".join(response_lines)

    return jsonify({"answer": answer, "sources": results})


if __name__ == "__main__":
    print("Starting local chatbot server at http://127.0.0.1:5000")
app.run(host="0.0.0.0", debug=True, port=5000)
