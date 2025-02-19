import requests
from bs4 import BeautifulSoup
import re
import html

def check_important_announcement():
    url = "https://www.desotocountyschools.org/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Failed to fetch the webpage.")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Search for the specific school closure message pattern
    closure_message_pattern = re.compile(r'<h3><strong>Due.*?</strong></h3>', re.IGNORECASE)
    
    # Look for all instances that match the pattern
    matches = closure_message_pattern.findall(str(soup))
    
    if matches:
        for match in matches:
            # Remove HTML tags and decode HTML entities
            clean_message = re.sub(r'<.*?>', '', match)
            clean_message = html.unescape(clean_message)
            print("School Closure Notice:", clean_message)
    else:
        print("No school closure announcements found.")

if __name__ == "__main__":
    check_important_announcement()
