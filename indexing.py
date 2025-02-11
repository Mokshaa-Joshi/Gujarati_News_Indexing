import requests
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
import re
from datetime import datetime


# MongoDB connection setup
client = MongoClient("mongodb+srv://aieworldsportso2o:a8T5wYHiQp0EuNpa@cluster0.n3a1w.mongodb.net/")  
db = client['news_data']  # Database name
gs_collection = db['gujarat_samachar_articles']  # Collection for Gujarat Samachar
dd_collection = db['dd_news_articles']  # Collection for DD News Gujarati

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Function to scrape articles from Gujarat Samachar
def scrape_gujarat_samachar():
    base_url = "https://www.gujaratsamachar.com/"
    response = requests.get(base_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve Gujarat Samachar. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    today_date = datetime.today().strftime('%Y-%m-%d')

    for article in soup.find_all('div', class_='news-box'):
        title = article.find('a', class_='theme-link news-title').text.strip()
        link = article.find('a', class_='theme-link')['href']
       # summary = article.find('p').text.strip() if article.find('p') else ""
        
        if link.startswith('/'):
            link = base_url + link
        
        content = scrape_article_content(link)
        
        if title and link and content:
            articles.append({
                'title': title,
                'date': today_date,
                'link': link,
                'content': content
            })
    
    return articles


# Function to scrape articles from DD News Gujarati
def scrape_dd_news():
    base_url = "https://ddnewsgujarati.com/about/news-archive/"
    response = requests.get(base_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve DD News Gujarati. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    
    for article in soup.find_all('div', class_='views-field views-field-nid views-field-changed'):
        title_tag = article.find('p', class_='archive-title')
        date_tag = article.find('p', class_='archive-date')  # Extract date
        link_tag = article.find('a')

        if not title_tag or not link_tag or not date_tag:
            continue

        title = title_tag.text.strip()
        date = date_tag.text.strip()  # Extract text from <p> tag
        link = link_tag['href']

        if link.startswith('/'):
            link = "https://ddnewsgujarati.com" + link  

        content = scrape_article_content(link)
        
        if title and link and content:
            articles.append({
                'title': title,
                'date': date,  # Store only text, not the tag itself
                'link': link,
                'content': content
            })

    return articles



# Function to scrape article content
def scrape_article_content(link):
    try:
        response = requests.get(link, headers=headers)
        if response.status_code != 200:
            return "Error loading article content."
        
        soup = BeautifulSoup(response.content, 'html.parser')
        content_elements = soup.find_all(['p'])
        full_text = ' '.join([element.get_text().strip() for element in content_elements])

        # Extract only Gujarati text using regex
        gujarati_text = ' '.join(re.findall(r'[\u0A80-\u0AFF]+', full_text))

        return gujarati_text if gujarati_text else "Gujarati content not available."
    except Exception as e:
        return f"Error: {e}"


# Function to store articles in MongoDB, avoiding duplicates
def store_in_mongodb(articles, collection, source):
    if not articles:
        print(f"No new articles from {source}.")
        return

    for article in articles:
        if collection.find_one({'link': article['link']}):
            print(f"Article already exists in {source}")
        else:
            try:
                collection.insert_one(article)
                print(f"Inserted in {source}")
            except Exception as e:
                print(f"Error inserting article in {source}: {e}")

# Main function to scrape and store data from both websites
def main():
    gujarat_samachar_articles = scrape_gujarat_samachar()
    dd_news_articles = scrape_dd_news()
    
    store_in_mongodb(gujarat_samachar_articles, gs_collection, "Gujarat Samachar")
    store_in_mongodb(dd_news_articles, dd_collection, "DD News Gujarati")

if __name__ == "__main__":
    main()
