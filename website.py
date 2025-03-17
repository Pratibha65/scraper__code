from serpapi.google_search import GoogleSearch
from urllib.parse import urlparse
from typing import Optional
from linkedin_details import get_search_results

def generate_website_query(consignee_name: str, location: str) -> str:
    return f'{consignee_name} official website OR homepage OR "about us" OR "about.me" AND {location}'

# Extract official website
def get_official_website(consignee_name: str, location: str) -> Optional[str]:
    website_url = None
    consignee_terms = consignee_name.lower().split()

    # Get search results from SerpAPI
    search_results = get_search_results(generate_website_query(consignee_name, location))

    # Score each result based on various factors
    scored_results = []
    for result in search_results[:5]:  # Look at top 5 results
        score = 0
        link = result["link"].lower()
        parsed_url = urlparse(link)
        domain = parsed_url.netloc
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()

        # Highest priority: Exact company name in domain
        if consignee_name.lower().replace(" ", "") in domain.replace("www.", ""):
            score += 15  

        # Check if all terms from consignee name appear in domain
        if all(term in domain.replace("www.", "") for term in consignee_terms):
            score += 12  

        # Check for exact company name in title
        if consignee_name.lower() in title:
            score += 8

        # Check for all terms in title
        if all(term in title for term in consignee_terms):
            score += 6

        # Bonus for official indicators in title or snippet
        official_indicators = ["official", "homepage", "about us", "contact", "home", "welcome to"]
        if any(indicator in title for indicator in official_indicators):
            score += 5
        if any(indicator in snippet for indicator in official_indicators):
            score += 4

        # Heavy penalty for known non-official domains
        non_official_domains = {
            "facebook.com", "linkedin.com", "twitter.com", "instagram.com", 
            "youtube.com", "crunchbase.com", "bloomberg.com", "yelp.com",
            "indeed.com", "glassdoor.com", "bbb.org", "wikipedia.org", "volza.com"
        }
        if domain.endswith(tuple(non_official_domains)):
            score -= 20  

        # Bonus for common official TLDs
        if domain.endswith(('.com', '.org', '.net', '.co')):
            score += 2

        official_subpages = {"about-us", "contact", "home", "official"}
        subdirs = link.split('/')[3:]  # Extract subdirectories

        # Penalty for subdirectories
        if len(subdirs) > 2 and not any(sub in subdirs for sub in official_subpages):
            score -= min(5, len(subdirs))  # Reduce penalty if it's an official page



        # Store result with its metadata for debugging
        scored_results.append({'score': score, 'link': link, 'domain': domain, 'title': title})

    # Sort by score in descending order
    scored_results.sort(reverse=True, key=lambda x: x['score'])

    # Debug info
    print(f"\nDebug info for {consignee_name}:\n**********************************************************\n")
    for idx, result in enumerate(scored_results[:5]):
        print(f"{idx + 1}. Score: {result['score']}, Domain: {result['domain']}")
        print(f"   Title: {result['title']}")
        print(f'   URL: {result['link']}\n\n')
        

    # Return the highest scored result if it meets minimum threshold
    if scored_results and scored_results[0]['score'] > 10:
        website_url = scored_results[0]['link']
    else:
        print(f"No suitable website found for {consignee_name}\n\n")

    return website_url

get_official_website(" ROYAL DOHA TRADING CONTRACTING AND SERVICES WLL","Doha") 