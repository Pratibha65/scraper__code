import os
import time 
import pandas as pd
from dotenv import load_dotenv
from linkedin_details import get_company_details
from website import get_official_website
from contacts import extract_contacts, search_contacts
load_dotenv()
api_key = os.getenv('SERP_API_KEY')  
print(api_key)



def Read_Consignee(file_path: str) -> None:
    df=pd.read_csv(file_path)
    
    df["LinkedIn URL"] = None
    df["LinkedIn Connected People"] = None
    df["Company Website"] = None
    # df["Company Location"] = None
    df["Phone Numbers"] = None
    df["Email"]= None
    
    for idx,row in df.iterrows():
        consignee_name = row["Consignee_Name"]
        location = row["Location"]
        print(f"Processing: {consignee_name} from {location}----------------------------------->\n")

        # Fetch LinkedIn data using Serper
        linkedin_url, linkedin_connected_people = get_company_details(consignee_name,location)
        
        # Find company's official website
        website_url = get_official_website(consignee_name,location)

        # Update DataFrame with LinkedIn and website information
        df.at[idx, "LinkedIn URL"] = linkedin_url
        df.at[idx, "Company Website"] = website_url
        df.at[idx, "LinkedIn Connected People"] = ", ".join(linkedin_connected_people)
        # df.at[idx, "Company Location"] = ", ".join(company_locations)

        # Extract contact details if website is found
        # phones, emails = [],[]
        if website_url: 
            phones, emails = extract_contacts(website_url)
            df.at[idx, "Phone Numbers"] = ", ".join(phones)
            df.at[idx, "Email"] = ", ".join(emails)
            if not phones or not emails:
                s_phones, s_emails = search_contacts(consignee_name, location)
                # Merge phones
                if not phones:
                    phones = s_phones
                # Merge emails

                if not emails:
                    emails = s_emails
                df.at[idx, "Phone Numbers"] = ", ".join(phones)
                df.at[idx, "Email"] = ", ".join(emails)

        # Implement rate limiting to avoid API blocks
        time.sleep(2)
 
    # Save enriched data to a new CSV file
    output_file = 'Consignee_Info.csv'
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")   

    
if __name__ == '__main__':
    Read_Consignee("consignee.csv")