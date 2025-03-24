import re
import requests
from bs4 import BeautifulSoup
import random
import os
import time
from urllib.parse import urljoin

SERP_API_KEY = os.getenv("SERP_API_KEY")

DEBUG = True

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
]

DEFAULT_HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

# url="https://royaldohatrading.com/contact.php"
def extract_contacts(url,retries = 3):
    try:
        session = requests.Session()
        headers = DEFAULT_HEADERS.copy()
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        for attempt in range(retries):
            print(f"*******\nFetching URL: {url}  (Attempt {attempt + 1})\n")
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

            if response.status_code == 403:
                print("❌ 403 Forbidden! Retrying with a different User-Agent...") if DEBUG else None
                time.sleep(2)
                continue

        print(f"***************************************\nResponse Status Code: {response.status_code}\n")

        
        
        if response.status_code != 200:
            # print(f"-----------------------------------\nFailed to fetch page. Response: {response.text[:200]}\n")
            # print(response.text[:500])
            return [], []

        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find("meta", attrs={"http-equiv": "refresh"})
        

        # If the response is an HTML page with a meta refresh, extract the new URL
        # if meta_tag and "URL=" in meta_tag["content"]:
        #     new_url = meta_tag["content"].split("URL=")[-1].strip()
        #     print(f"Redirect detected! Fetching new URL: {new_url}\n")
        #     response = requests.get(new_url, headers=headers, timeout=10)


        if response.status_code != 200:
            # print(f"-----------------------------------\nFailed to fetch page. Response: {response.text[:200]}\n")
            # print(response.text[:500])
            return False

        # If the response is an HTML page with a meta refresh, then extract the new URL
        if meta_tag:
            content = meta_tag.get("content", "")
            if "URL=" in content:
                new_url = urljoin(url, content.split("URL=")[-1].strip())
                print(f"Redirect detected! Fetching new URL: {new_url}") if DEBUG else None
                return extract_contacts(new_url, retries=3)         

        
        text = soup.get_text()
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        
        phone_pattern = r'(?:(?:\+|00)\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'

        phones = re.findall(phone_pattern, text)

        print(f"------\nExtracted {len(phones)} phone numbers and {len(emails)} emails\n")

        print(list(phones))
        print("___________________")
        print(list(emails))

        return list(set(phones)), list(set(emails))
    except Exception as e:
        print(f"Error extracting contacts: {e}")
        return [], []

def search_contacts(consignee, location):
    query = (
        f'{consignee} email OR phone OR contact site:company.com OR site:official OR site:about.me '
        f'OR site:contact.com "{location}"'
    )

    print(f"\nSearch Query: {query}\n") if DEBUG else None

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
        response.raise_for_status()  
        results = response.json().get("organic", [])

        print(f"Found {len(results)} search results") if DEBUG else None

        phones, emails = [], []
        for result in results:
            url = result.get("link", "")
            if not url:
                print("\nSkipping empty URL.\n")
                continue

            print(f"Processing result: {url}")
            new_phones, new_emails = extract_contacts(url, retries=3)
            phones.extend(new_phones) 
            emails.extend(new_emails)

        phones, emails = list(set(phones)), list(set(emails))

        print(f"___________________________________________________________\nTotal unique phones: {phones}, Total unique emails: {emails}\n\n")
        return phones, emails

    except Exception as e:
        print(f"Error fetching search results: {e}")
        return [], []

# Test function


# extract_contacts(url, retries=3)