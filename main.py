import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://resparkit.com"
BLOG_URL = "https://resparkit.com/blogs"
OUTPUT_FILE = Path(__file__).resolve().parent / "articles.json"


def scrape_resparkit_articles():
    print(f"Fetching blog index from {BLOG_URL}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(BLOG_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Network error accessing Resparkit: {e}")
        save_fallback_articles()
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/blogs/" in href and href != "/blogs":
            full_url = href if href.startswith("http") else BASE_URL + href
            links.add(full_url)

    print(f"Found {len(links)} blog links. Scraping content...")
    articles_data = []

    for url in links:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            article_soup = BeautifulSoup(res.text, "html.parser")

            title_tag = article_soup.find("h1") or article_soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"

            paragraphs = article_soup.find_all("p")
            text = "\n".join(
                [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            )

            if text:
                articles_data.append({"title": title, "url": url, "text": text})
                print(f"Scraped: {title}")
        except Exception as err:
            print(f"Skipped {url} due to error: {err}")

    if not articles_data:
        save_fallback_articles()
    else:
        with OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(articles_data)} articles to {OUTPUT_FILE}")


def save_fallback_articles():
    print("Using default curated articles as fallback...")
    articles_data = [
        {
            "title": "Grimmoji: the free browser game where every square hides a surprise",
            "url": "https://resparkit.com/blogs",
            "text": "A free browser game where every tap reveals something new. Collect emoji sets, earn platform credit, and start with 50 free tokens. No download needed.",
        },
        {
            "title": "SmartLink: A New Way to Hype Your Audio and Video Release",
            "url": "https://resparkit.com/blogs",
            "text": "Resparkit is a central hub for creators to showcase their multimedia content, enabling fans to access everything from music to videos behind one clean link.",
        },
    ]
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=4)
    print(f"Saved fallback articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape_resparkit_articles()
