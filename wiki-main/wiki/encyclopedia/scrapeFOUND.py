import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed


def scrape():

    # Path to ChromeDriver
    chrome_driver_path = 'C:/Users/lovro/Downloads/chromedriver-win644/chromedriver-win64/chromedriver.exe'

    # Load the locations data from the JSON file
    with open('C:/Users/lovro/Downloads/WIKI/wiki/encyclopedia/w11.json', 'r', encoding='utf-8') as f:
        locations = json.load(f)

    # Function to create a new WebDriver instance without a proxy
    def create_driver():
        chrome_options = Options()
        chrome_options.add_argument('--headless=old')  # Enable headless mode
        chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration for headless mode
        chrome_options.add_argument('--window-size=1920x1080') 
        chrome_options.add_argument("--log-level=3")# Set window size for headless
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(5)
        return driver

    def append_to_json_lines_file(filename, new_data):
        # Open the file in append mode and write each entry as a separate JSON object on a new line
        with open(filename, 'a', encoding='utf-8') as f:
            for entry in new_data:
                json_line = json.dumps(entry, ensure_ascii=False)
                f.write(json_line + '\n')

    # Function to safely extract text from an element if it exists
    def safe_find_text(element, selector):
        found_elements = element.find_elements(By.CSS_SELECTOR, selector)
        if found_elements:
            return found_elements[0].text
        else:
            return "N/A"

    # Function to scrape a single location's ads
    def scrape_location(location):
        driver = create_driver()
        
        location_id = location['id']
        
        base_url = "https://www.index.hr/oglasi/nekretnine/prodaja-stanova/pretraga?searchQuery=%257B%2522category%2522%253A%2522prodaja-stanova%2522%252C%2522module%2522%253A%2522nekretnine%2522%252C%2522includeSettlementIds%2522%253A%255B%2522{location_id}%2522%255D%252C%2522sortOption%2522%253A4%257D"
        url = base_url.format(location_id=location_id)
        driver.get(url)

        ad_count_element = driver.find_element(By.CLASS_NAME, "headerDesktop__searchResult___1uh7t")

        # Then, find the specific span element inside it that contains the number
        ad_count_number = ad_count_element.find_element(By.TAG_NAME, "span").text

        # Clean up the extracted text to ensure only the number is retrieved
        print(ad_count_number.split(" ")[1])
        ad_count = ad_count_number.split(" ")[1]

        driver.close()
        driver.quit()
        return int(ad_count)

    def append_data_length_to_file(file_name, location, data_len):
        # Open the file in append mode and write the data length
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(f"{location}: {data_len}\n")

    # Main function to manage parallel scraping
    # Main function to manage parallel scraping
    def main():
        # Use ThreadPoolExecutor to manage parallel execution of scraping
        with ThreadPoolExecutor(max_workers=3) as executor:  # Consider lowering max_workers
            futures = {executor.submit(scrape_location, location): location for location in locations}
            for i, future in enumerate(as_completed(futures), start=1):
                
                append_data_length_to_file('data_lengths.txt', futures[future]['name'], future.result())
                    
                

    main()
