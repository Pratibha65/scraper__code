import re
import requests
from bs4 import BeautifulSoup
import random
import os

SERP_API_KEY = os.getenv("SERP_API_KEY")


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
]

url="https://royaldohatrading.com/contact.php"
def extract_contacts(url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        print(f"***************************************\nFetching URL: {url}\n")
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"***************************************\nResponse Status Code: {response.status_code}\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find("meta", attrs={"http-equiv": "refresh"})
        
        # If the response is an HTML page with a meta refresh, extract the new URL
        # if meta_tag and "URL=" in meta_tag["content"]:
        #     new_url = meta_tag["content"].split("URL=")[-1].strip()
        #     print(f"Redirect detected! Fetching new URL: {new_url}\n")
        #     response = requests.get(new_url, headers=headers, timeout=10)


        if response.status_code != 200:
            print(f"-----------------------------------\nFailed to fetch page. Response: {response.text[:200]}\n")
            print(response.text[:500])
            return [], []
        
        text = BeautifulSoup(response.text, 'html.parser').get_text()
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        phones = re.findall(r'(?:\+?\d{1,3}[-.\s]?)?' \
              r'(?:\(?\d{2,4}\)?[-.\s]?)?' \
              r'\d{3,4}[-.\s]?\d{3,4}' \
              r'(?:\s*(?:ext\.?|x)\s*\d{1,5})?', text)
        
        print(f"-----------------------------------------\nExtracted {len(phones)} phone numbers and {len(emails)} emails\n")
        print(list(phones))
        print("___________________")
        print(list(emails))
        return list(phones), list(emails)
    except Exception as e:
        print(f"Error extracting contacts: {e}")
        return [], []

def search_contacts(consignee, location):
    query = f'{consignee} contact email phone site:linkedin.com OR site:facebook.com OR site:yellowpages.com'
    print(f"\nSearch Query: {query}\n")
    headers = {
        "X-API-KEY": SERP_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "q": query,
        "num": 5
    }
    
    try:
        response = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
        response.raise_for_status()  # Raise an error if request fails
        results = response.json().get("organic", [])

        print(f"Found {len(results)} search results")

        phones, emails = [], []
        for result in results:
            url = result.get("link", "")
            if not url:
                print("\nSkipping empty URL.\n")
                continue

            print(f"Processing result: {url}")
            new_phones, new_emails = extract_contacts(url)
            phones.extend(new_phones) 
            emails.extend(new_emails)

        print(f"___________________________________________________________\nTotal unique phones: {len(set(phones))}, Total unique emails: {len(set(emails))}\n\n")
        return list(phones), list(emails)

    except Exception as e:
        print(f"Error fetching search results: {e}")
        return [], []

# Test function


extract_contacts(url)