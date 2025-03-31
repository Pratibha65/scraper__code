import os
from typing import List, Tuple, Optional
import requests
from dotenv import load_dotenv


def loadEnv() -> str:
    load_dotenv()
    SERP_API_KEY = os.getenv("SERP_API_KEY")

    if not SERP_API_KEY:
        raise ValueError("SERP_API_KEY is missing! Please check your .env file.")
    
    return SERP_API_KEY

SERP_API_KEY = loadEnv()
DEBUG = True

if DEBUG:
    print(f'******************************************\n{SERP_API_KEY}\n*********************************************\n')

def generate_companylinkedin_query(consignee_name:str , location: str) -> str:
    return f'{consignee_name} site:linkedin.com/company "{location}"'

def generate_peoplelinkedin_query(consignee_name:str , location: str) -> str:
    return (
        f'{consignee_name} site:linkedin.com/in OR site:linkedin.com/pub'
        f'("Sales" OR "Managing Director" OR "CEO" OR "Business Development" OR "Marketing" OR "Operations" OR "Procurement" OR "Supply Chain" OR "Partnerships" OR "Founder" OR "Owner" OR "CFO" OR "COO")'
        f'("{location}" OR "headquarters")'
    )



def get_search_results(query: str) -> list[dict]:

    try:
        headers = {
            "X-API-KEY": SERP_API_KEY,  
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": 10
        }

        response = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
        response.raise_for_status()  # HTTP errors

        results = response.json()
        return results.get("organic", [])  # Extract organic search results
    except Exception as e:
        print(f"\nError fetching search results: {e}\n")
        return []

def get_company_details(consignee_name: str, location: str) -> tuple[Optional[str], list[str]]:
    linkedin_url, linkedin_connected_people = None, []
    # company_locations = []
    search_company_results = get_search_results(generate_companylinkedin_query(consignee_name,location)) 
    search_people_results = get_search_results(generate_peoplelinkedin_query(consignee_name,location))

    
   

    for result in search_company_results:
        link = result.get("link", "")
        #linkedin company page
        if '/company' in link and not linkedin_url:
            linkedin_url = link           

        #linkedin people page    
        if '/in' in link:
            linkedin_connected_people.append(link) 
 
    
    linkedin_connected_people.extend([res["link"] for res in search_people_results if "link" in res])
    
    return linkedin_url, linkedin_connected_people 

# get_company_details(" ROYAL DOHA TRADING CONTRACTING AND SERVICES WLL","Doha") 
 