import feedparser
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
from bs4 import BeautifulSoup
import argparse
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Global variables
RSS_FEED_URL = "http://rss.cnn.com/rss/cnn_topstories.rss"  # Example: CNN Top Stories
DEBUG = True  # Debug flag to enable printing progress messages

def fetch_rss_articles():
    """
    Fetch articles from the RSS feed and extract title and link for each.
    
    Returns:
    list of tuples: Each tuple contains (title, link) for an article
    """
    if DEBUG:
        print("Fetching RSS articles...", flush=True)
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        articles.append((title, link))

    if DEBUG:
        print(f"Fetched {len(articles)} articles", flush=True)
    return articles

def choose_most_interesting_article(articles):
    """
    Use OpenAI GPT to choose the most interesting article.
    
    Returns:
    tuple: (title, link) of the most interesting article
    """
    # if DEBUG:
    #     print("Choosing the most interesting article...", flush=True)
    titles = [article[0] for article in articles]
    print(titles, flush=True)
    # prompt = f"From these news titles, choose the most interesting one:\n{titles}\nMost interesting title:"

    # response = client.chat.completions.create(
    #     model="chatgpt-4o-latest",
    #     messages=[
    #         {"role": "system", "content": "You are a news editor tasked with selecting the most interesting headline. You must choose one."},
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=50
    # )

    # chosen_title = response.choices[0].message.content.strip()

    # if DEBUG:
    #     print(f"Chosen article title: {chosen_title}", flush=True)
    # return chosen_title
    
    # return all titles for now
    return titles

def read_article_content(url):
    """
    Fetch and parse the content of the article.
    
    Returns:
    str: The main content of the article
    """
    if DEBUG:
        print(f"Reading article content from {url}", flush=True)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # This is a simple extraction and might need to be adjusted based on the website's structure
    paragraphs = soup.find_all('p')
    content = ' '.join([p.text for p in paragraphs])

    if DEBUG:
        print(f"Article content length: {len(content)} characters", flush=True)
    return content

def generate_poem(article_title):
    """
    Use OpenAI GPT to generate a humorous poem based on the article content.
    
    Returns:
    str: A humorous poem summarizing the article
    """
    if DEBUG:
        print("Generating poem...", flush=True)
    prompt = f"Write a poem based on the following set of news headlines. You have exactly 4 lines. Remember that each line cannot exceed 18 characters including spaces and punctuation. Check your work carefully. Output only the poem, and nothing else. Poem: \n{article_title}\n"

    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": "You are a creative poet tasked with summarizing news headlines as humorous poetry. Your speciality is all of your poems are 4 lines long, and no single line of poetry can be longer than 18 characters including spaces and punctuation."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    initial_poem = response.choices[0].message.content.strip()
    final_poem = initial_poem
    
    if DEBUG:
        print("Initial poem generated", flush=True)

    # Second call to GPT to ensure poem fits the constraints
    rewrite_prompt = f"Rewrite this poem to ensure it has exactly 4 lines, and each line is no more than 18 characters including spaces and punctuation. Do this step by step, and check your work, but only output the final poem:\n\n{initial_poem}\n\nRewritten poem:"

    rewrite_response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {"role": "system", "content": "You are a poetry editor. Your task is to rewrite poems to fit specific constraints without losing their essence."},
            {"role": "user", "content": rewrite_prompt}
        ],
        max_tokens=500
    )

    final_poem = rewrite_response.choices[0].message.content.strip()
    if DEBUG:
        print("Final poem generated", flush=True)
    return final_poem

def crop_string(text, max_lines, max_chars_per_line):
    """
    Crop a string to a maximum number of lines and characters per line.

    Args:
    text (str): The input string to crop.
    max_lines (int): The maximum number of lines to keep.
    max_chars_per_line (int): The maximum number of characters per line.

    Returns:
    str: The cropped string.
    """
    lines = text.split('\n')
    cropped_lines = []

    for i, line in enumerate(lines):
        if i >= max_lines:
            break
        cropped_lines.append(line[:max_chars_per_line])

    return '\n'.join(cropped_lines)


def write_poem_to_file(poem, output_folder):
    """
    Write the generated poem to a file in the specified output folder.
    """

    if DEBUG:
        print("\nBefore crop:\n", poem, flush=True)
    poem = crop_string(poem, 4, 22)
    if DEBUG:
        print("\nAfter crop:\n", poem, flush=True)

    if DEBUG:
        print(f"Writing poem to file in {output_folder}...", flush=True)
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, "news_poem.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        current_date = datetime.now().strftime("---%B %d---\n").upper()
        f.write(current_date)
        f.write(poem)
    if DEBUG:
        print(f"Poem written to {file_path}", flush=True)

if __name__ == "__main__":
    if DEBUG:
        print("Starting newsPoem.py", flush=True)

    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate a news poem and save it to a file.")
    parser.add_argument("-o", "--output", default=".", help="Output folder for the poem file")
    args = parser.parse_args()

    articles = fetch_rss_articles()
    most_interesting_article_title = choose_most_interesting_article(articles)

    if most_interesting_article_title:
        poem = generate_poem(most_interesting_article_title)
        print(poem)
        write_poem_to_file(poem, args.output)
    else:
        print("No interesting article found.")
    
    if DEBUG:
        print("newsPoem.py completed", flush=True)
