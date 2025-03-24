import os
import time 
import pandas as pd
from linkedin_details import get_company_details
from website import get_official_website
from contacts import extract_contacts, search_contacts

def Read_Consignee(file_path: str) -> None:
    try:
        df=pd.read_csv(file_path)
    except FileNotFoundError:
        print(f'Error: File {file_path} not found.')
        return
    
    required_col = {"Consignee_Name", "Location"}
    if not required_col.issubset(df.columns):
        print(f"Error: Missing required columns {required_col - set(df.columns)} in input file.")
        return
    
    df["LinkedIn URL"] = None
    df["LinkedIn Connected People"] = None
    df["Company Website"] = None
    df["Phone Numbers"] = None
    df["Email"]= None
    
    for idx,row in df.iterrows():
        consignee_name = row.get("Consignee_Name", "").strip()
        location = row.get("Location", "").strip()

        if not consignee_name or not location:
            print(f"Skipping row {idx} due to missing consignee name or location.")
            continue

        print(f"Processing: {consignee_name} from {location}----------------------------------->\n")

        try:
            linkedin_url, linkedin_connected_people = get_company_details(consignee_name,location)
            
            # Find company's official website
            website_url = get_official_website(consignee_name,location)

            # Update DataFrame with LinkedIn and website information
            df.at[idx, "LinkedIn URL"] = linkedin_url
            df.at[idx, "Company Website"] = website_url
            df.at[idx, "LinkedIn Connected People"] = ", ".join(linkedin_connected_people)
            # df.at[idx, "Company Location"] = ", ".join(company_locations)

            # Extract contact details if website is found
            phones, emails = [],[]
            if website_url: 
                phones, emails = extract_contacts(website_url, retries=3)
                if phones:
                    df.at[idx, "Phone Numbers"] = ", ".join(phones)
                if emails:
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
        except Exception as e:
            print(f"Error processing {consignee_name}: {e}")

        
        time.sleep(2)
 
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file = 'Consignee_Info.csv'
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file} at {timestamp}")   

    
if __name__ == '__main__':
    Read_Consignee("Consignee.csv")