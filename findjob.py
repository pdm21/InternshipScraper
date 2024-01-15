# Google Sheets API - Google Cloud
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Web Scraping Libraries
import requests
from bs4 import BeautifulSoup

# Define the internship class for objects
class Internships():
    def __init__(self, company, location, position):
        self.company = company
        self.location = location
        self.position = position
        self.status = 'NA' # NA = not applied. This will be updated automatically through updates to google sheets spreadsheet via Google Cloud API
    def applicationStatus(self):
        return self.status
    def printInfo(self):
        print(self.company, " ", self.location, " ", self.position)

# Send a GET request to the repository URL
url = "https://github.com/pittcsc/Summer2024-Internships#the-list-"
response = requests.get(url)

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find all the <td> tags within the repository
tr_tags = soup.find_all('tr')
td_tags = soup.find_all('td')

companies = []
locations = [] # R = remote, N = new york, B = boston, C = california, D = DC, O = other
positions = [] # position as listed, string may be shortened based off of a key in future
internships = []
# Creating a list of companies
for x in range(0, len(td_tags), 3):
    companies.append(td_tags[x].text.strip())
# Creating a list of locations, consistent with indices prior
for x in range(1, len(td_tags), 3):
    locations.append(td_tags[x].text.strip())
# Creaating a list of positions / notes
for x in range(2, len(td_tags), 3):
    positions.append(td_tags[x].text.strip())
    
# Creating all the internship objects
for x in range(len(companies)):
    intern = Internships(companies[x], locations[x], positions[x])
    internships.append(intern)


print(f"There are a total of {len(companies)} internships in the list.")

# API Code

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "1Byg6CWrxoCvFlkEhYRRYNWQbZjMo3W1Wh7lwKfWlGxg"

def main():
    credentials = None
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not credentials or not credentials.valid: # if we do not have credentials, or if they are invalid
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port = 0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())
    
    try: 
        service = build("sheets", "v4", credentials = credentials)
        sheets = service.spreadsheets()

        def company_exists(company):
            result = sheets.values().get(
                spreadsheetId=SPREADSHEET_ID,
                range="Internships '24!A3:A"
            ).execute()

            values = result.get('values', [])

            for row in values:
                if row and row[0] == company:
                    return True
            return False

        # Create a list of values to append to the spreadsheet
        values = []
        for intern in internships:
            if not company_exists(intern.company):
                values.append([intern.company, intern.location]) # took out position, as there is no consistency in this output

        # Append the values to the spreadsheet
        if len(values) > 0:
            sheets.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range="Internships '24!A2",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values}
            ).execute()
            print("Data has been added to the spreadsheet.")
        else:
            print("No new data added. Data is up to date.")

    except HttpError as error:
        print(error)

if __name__ == "__main__":
    main()