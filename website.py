import os
import requests
from urllib.parse import urlparse, urljoin
from typing import Optional
from bs4 import BeautifulSoup
import re
import time
import httpx
from linkedin_details import get_search_results

def generate_website_query(consignee_name: str, location: str) -> str:
    return f'{consignee_name} official website OR homepage OR "about us" OR "about.me" "{location}"'

def get_official_website(consignee_name: str, location: str) -> Optional[str]:
    website_url = None
    consignee_terms = consignee_name.lower().split()
    location_terms = location.lower().split()

   
    search_results = get_search_results(generate_website_query(consignee_name, location))

    
    skip_domains = {
        "volza.com", "eximpedia.app", "tradeatlas.com", "trademo.com", "atom.com"
    }

    
    scored_results = []
    for result in search_results[:5]:  
        score = 0
        link = result.get("link", "").lower()
        parsed_url = urlparse(link)
        domain = parsed_url.netloc
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()

        
        if any(domain.endswith(nd) for nd in skip_domains):
            print(f"⏩ Skipping {domain} (Unwanted domain)")
            continue  

        print(f"\n🔍 Evaluating: {link}")
        print(f"🔹 Initial Score: {score}")

        # company name in domain
        clean_domain = domain.replace("www.", "")
        if consignee_name.lower().replace(" ", "") in clean_domain:
            score += 15  
            print(f"✅ +15 (Company name in domain) | New Score: {score}")

        #  terms from consignee name appear in domain
        if all(term in clean_domain for term in consignee_terms):
            score += 12  
            print(f"✅ +12 (All terms from consignee in domain) | New Score: {score}")

        # company name in title
        if consignee_name.lower() in title:
            score += 8
            print(f"✅ +8 (Company name in title) | New Score: {score}")

        # terms in title
        if all(term in title for term in consignee_terms):
            score += 6
            print(f"✅ +6 (All terms from consignee in title) | New Score: {score}")

        
        location_bonus = 10
        try:
            response = requests.get(link, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = " ".join(soup.stripped_strings).lower() 
                if any(loc in page_text for loc in location_terms):
                    score += location_bonus
                    print(f"{location_bonus} (Location found in webpage content) | New Score: {score}")
                else:
                    score -= 10  
                    print(f"-10 (Location not found in webpage) | New Score: {score}")
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")

        #official indicators in title or snippet
        official_indicators = ["official", "homepage", "about us", "contact", "home", "welcome to"]
        if any(indicator in title for indicator in official_indicators):
            score += 5
            print(f"+5 (Official indicator in title) | New Score: {score}")
        if any(indicator in snippet for indicator in official_indicators):
            score += 4
            print(f"+4 (Official indicator in snippet) | New Score: {score}")

       
        non_official_domains = {
            "facebook.com", "linkedin.com", "twitter.com", "instagram.com", 
            "youtube.com", "crunchbase.com", "bloomberg.com", "yelp.com",
            "indeed.com", "glassdoor.com", "bbb.org", "wikipedia.org"
        }
        if any(domain.endswith(nd) for nd in non_official_domains):
            score -= 20  
            print(f"-20 (Non-official domain detected: {domain}) | New Score: {score}")

        #common official TLDs
        official_tlds = {".com", ".org", ".net", ".co"}
        if any(domain.endswith(tld) for tld in official_tlds):
            score += 3
            print(f"+3 (Official TLD detected) | New Score: {score}")

        official_subpages = {"about-us", "contact", "home", "official"}
        subdirs = parsed_url.path.strip("/").split('/')  

        
        if len(subdirs) > 2 and not any(sub in subdirs for sub in official_subpages):
            penalty = min(5, len(subdirs))
            score -= penalty  
            print(f"-{penalty} (Too many subdirectories) | New Score: {score}")

        
        scored_results.append({'score': score, 'link': link, 'domain': domain, 'title': title})

   
    scored_results.sort(reverse=True, key=lambda x: x['score'])

 
    print(f"\n Final Scores for: {consignee_name}")
    print(f"{'='*60}")
    for idx, result in enumerate(scored_results[:5]):
        print(f"{idx + 1}. Score: {result['score']}, Domain: {result['domain']}")
        print(f"   Title: {result['title']}")
        print(f"   URL: {result['link']}\n")

    
    if scored_results and scored_results[0]['score'] > 10:
        website_url = scored_results[0]['link']
    else:
        print(f"No suitable website found for {consignee_name}\n")

    return website_url

def get_final_redirect_url(url: str) -> str:
    """
    Tries to get the final redirected URL using `requests` first.
    If `requests` fails, it retries using `httpx`.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

   
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"✅ `requests` Success: {response.url}")
        return response.url  # Return final redirected URL
    except requests.RequestException as e:
        print(f"⚠️ `requests` failed: {e}")

   
    try:
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url, headers=headers, timeout=10)
            print(f"✅ `httpx` Success: {response.url}")
            return response.url
    except httpx.RequestError as e:
        print(f"❌ `httpx` also failed: {e}")


    print(f"⚠️ Both `requests` and `httpx` failed. Returning original URL: {url}")
    return url  # Return original URL if there's an error


def find_contact_page(base_url: str) -> str:
    """
    Tries to find a 'Contact' page on the website, even if the site redirects.
    """
    try:
        final_url = get_final_redirect_url(base_url)  
        session = requests.Session()
        response = session.get(final_url, timeout=5)

        if response.status_code != 200:
            print(f"⚠️ Failed to load {final_url} (Status Code: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if "contact" in href or "contact-us" in href:
                contact_url = urljoin(final_url, link["href"])  
                print(f"✅ Found Contact Page: {contact_url}")
                return contact_url  

    except requests.RequestException as e:
        print(f"⚠️ Error fetching webpage: {e}")

    print(f"❌ No contact page found on {base_url}")
    return None

# Test Function
# get_official_website("ROYAL DOHA TRADING CONTRACTING AND SERVICES WLL", "Doha")
