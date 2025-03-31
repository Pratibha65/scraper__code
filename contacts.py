import re
import requests
from bs4 import BeautifulSoup
import random
import os
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Auto WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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


def get_dynamic_content(url):
    """Fetch page source using Selenium for JavaScript-rendered content."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(url)
    
    try:
        # Wait for JavaScript to load (adjust as needed)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception:
        print("Warning: Page load timeout!")

    page_source = driver.page_source
    driver.quit()
    return page_source

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

        
        html_content = response.text
        if "<script>" in html_content or "<div" in html_content:  # Possible JS content
            html_content = get_dynamic_content(url)  # Fetch with Selenium


        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find("meta", attrs={"http-equiv": "refresh"})
        
        # If the response is an HTML page with a meta refresh, then extract the new URL
        if meta_tag:
            content = meta_tag.get("content", "")
            if "URL=" in content:
                new_url = urljoin(url, content.split("URL=")[-1].strip())
                print(f"Redirect detected! Fetching new URL: {new_url}") if DEBUG else None
                return extract_contacts(new_url, retries=3)         
        
        text = soup.get_text()
        # emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)


        # Extract emails
        # Extract emails and phones from whole page
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', soup.get_text())
        phone_pattern = r'(?:(?:\+|00)\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
        phones = re.findall(phone_pattern, soup.get_text())
        
        # Extract from footer
        footer_emails, footer_phones = extract_from_footer(soup)
        
        # Combine results
        all_emails = list(set(emails + footer_emails))
        all_phones = list(set(phones + footer_phones))
        
        print(f"------\nExtracted {len(all_phones)} phone numbers and {len(all_emails)} emails\n")
        return all_phones, all_emails
    except Exception as e:
        print(f"Error extracting contacts: {e}")
        return [], []
    

def extract_emails(soup):
    """Extract emails from the webpage."""
    email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = set(re.findall(email_regex, soup.get_text()))

    # Extract from mailto links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("mailto:"):
            emails.add(href.replace("mailto:", "").strip())

    # Fix obfuscated emails
    obfuscated_patterns = [
        (r"\s*\[at\]\s*", "@"),
        (r"\s*\[dot\]\s*", "."),
        (r"\s*\(at\)\s*", "@"),
        (r"\s*\(dot\)\s*", "."),
        (r"\s*AT\s*", "@"),
        (r"\s*DOT\s*", ".")
    ]
    
    cleaned_emails = set()
    for email in emails:
        for pattern, replacement in obfuscated_patterns:
            email = re.sub(pattern, replacement, email)
        cleaned_emails.add(email)
    
    return list(cleaned_emails)


# def extract_from_footer(soup):
#     """Extract emails and phone numbers from footer section and print all extracted text."""
#     emails, phones = set(), set()
#     email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
#     phone_pattern = r'(?:(?:\+|00)\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
    
#     # Locate footer elements
#     # Locate footer elements
#     footers = soup.find_all("footer") + soup.find_all(class_=re.compile("footer", re.I)) + soup.find_all(class_=re.compile("footer-widget", re.I))
    
#     extracted_texts = set()
#     for footer in footers:
#         text = footer.get_text(" ", strip=True)  # Extract text with spaces
#         if text not in extracted_texts:
#             print(f"Extracted Footer Text: {text}\n")  # Print all text from footer elements
#             extracted_texts.add(text)
#         emails.update(re.findall(email_regex, text))
#         phones.update(re.findall(phone_pattern, text))
    
#     return list(emails), list(phones)


def clean_obfuscated_email(text):
    """Replace common email obfuscations like [at] → @ and [dot] → ."""
    obfuscated_patterns = [
        (r"\s*\[at\]\s*", "@"), 
        (r"\s*\[dot\]\s*", "."), 
        (r"\s*\(at\)\s*", "@"), 
        (r"\s*\(dot\)\s*", "."), 
        (r"\s*AT\s*", "@"), 
        (r"\s*DOT\s*", "."),
        (r"\s*email:\s*", "")  # Remove unnecessary prefixes
    ]
    for pattern, replacement in obfuscated_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def extract_from_footer(soup):
    """Extract and clean emails & phone numbers from the footer."""
    emails, phones = set(), set()
    
    email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
    phone_regex = r'(?:(?:\+|00)\d{1,3}[-.\s]?)?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'

    footers = soup.find_all("footer") + soup.find_all(class_=re.compile("footer", re.I))
    
    for footer in footers:
        text = " ".join(footer.stripped_strings)  
        cleaned_text = clean_obfuscated_email(text)  # 🔹 Fix obfuscation
        
        found_emails = re.findall(email_regex, cleaned_text)
        found_phones = re.findall(phone_regex, cleaned_text)
        
        emails.update(found_emails)
        phones.update(found_phones)

    return list(emails), list(phones)



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