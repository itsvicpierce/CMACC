import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import schedule
import datetime
import os

def fetch_and_parse(url):
    try:
        response = requests.get(url, timeout=10)  # Add a timeout for better error handling
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    return None

def extract_data(soup):
    if soup is None:  # Check if soup is None, which means an error occurred
        return []
    dogs = soup.find_all('div', class_='gridResult')
    dog_list = []
    for dog in dogs:
        try:
            dog_list.append({
                'Name': dog.find('span', class_='text_Name results').text.strip() if dog.find('span', class_='text_Name results') else 'N/A',
                'Gender': dog.find('span', class_='text_Gender results').text.strip() if dog.find('span', class_='text_Gender results') else 'N/A',
                'Breed': dog.find('span', class_='text_Breed results').text.strip() if dog.find('span', class_='text_Breed results') else 'N/A',
                'Age': dog.find('span', class_='text_Age results').text.strip() if dog.find('span', class_='text_Age results') else 'N/A',
                'Animal Type': dog.find('span', class_='text_Animaltype results').text.strip() if dog.find('span', class_='text_Animaltype results') else 'N/A',
                'Weight': dog.find('span', class_='text_Weight results').text.strip() if dog.find('span', class_='text_Weight results') else 'N/A',
                'Brought to Shelter': dog.find('span', class_='text_Broughttotheshelter results').text.strip() if dog.find('span', class_='text_Broughttotheshelter results') else 'N/A',
                'Located At': dog.find('span', class_='text_Locatedat results').text.strip() if dog.find('span', class_='text_Locatedat results') else 'N/A',
                'Kennel Location': dog.find('span', class_='text_KennelLocation results').text.strip() if dog.find('span', class_='text_KennelLocation results') else 'N/A',
                'Qualified For': dog.find('span', class_='text_ViewType results').text.strip() if dog.find('span', class_='text_ViewType results') else 'N/A'
            })
        except AttributeError as e:
            print(f"Error extracting data for one dog: {e}")
    return dog_list

def scrape_dog_data():
    base_url = 'https://24petconnect.com/CLTAdopt'
    index = 0
    all_dogs = []
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    while True:
        current_url = f"{base_url}?index={index}&at=DOG"
        print(f"[{datetime.datetime.now()}] Fetching data from index: {index}")
        soup = fetch_and_parse(current_url)

        if soup is None:  # If there was an error fetching the page, skip this iteration
            print("Error fetching page. Exiting loop.")
            break

        new_dogs = extract_data(soup)
        if not new_dogs:  # If no dogs found, assume end of data
            print("No more dogs found. Exiting loop.")
            break

        all_dogs.extend(new_dogs)
        index += 30  # Increment index to fetch next page
        time.sleep(1)  # Delay to prevent hitting the server too rapidly

    print(f"Total dogs fetched: {len(all_dogs)}")

    # Convert collected data to DataFrame
    dogs_at_shelter = pd.DataFrame(all_dogs)

    # Add a column for the date the script ran
    dogs_at_shelter['Scrape Date'] = current_date

    # Handling 'Age' by converting to numeric, coercing errors, and removing NaN values
    dogs_at_shelter['Age'] = pd.to_numeric(dogs_at_shelter['Age'], errors='coerce')

    # Check if the CSV file exists
    csv_file = 'dogs_at_shelter.csv'
    if os.path.exists(csv_file):
        # Load existing data and append the new data
        existing_data = pd.read_csv(csv_file)
        updated_data = pd.concat([existing_data, dogs_at_shelter], ignore_index=True)
        updated_data.to_csv(csv_file, index=False)
        print(f"[{datetime.datetime.now()}] Data appended to '{csv_file}'.")
    else:
        # Save as new file if it doesn't exist
        dogs_at_shelter.to_csv(csv_file, index=False)
        print(f"[{datetime.datetime.now()}] Data saved to '{csv_file}'.")

def schedule_job():
    # Schedule the job to run daily at 5:30 PM
    schedule.every().day.at("13:00").do(scrape_dog_data)

    print("Schedule started. Will scrape at 1pm daily...")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule_job()
