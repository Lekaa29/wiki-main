import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.common.exceptions import StaleElementReferenceException

# Your BrowserStack credentials
BROWSERSTACK_USERNAME = 'besplatnolajkuje_45gtX1'  # Replace with your BrowserStack username
BROWSERSTACK_ACCESS_KEY = 'qREKXEVMGzzbWz4z2kuq'  # Replace with your BrowserStack access key


# Load the locations data from the JSON file
with open('w11-lenfixed-stan-small-test.json', 'r', encoding='utf-8') as f: #w11-lenfixed-stan
    locations = json.load(f)

# Function to create a new WebDriver instance without a proxy
def create_driver():
    print("Creating BrowserStack driver...")  # Debugging print
    # BrowserStack remote URL
    BROWSERSTACK_URL = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"
    
    # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless=old')  # Run browser in headless mode
    chrome_options.add_argument('--disable-gpu')  # Disable GPU to avoid issues in headless mode
    chrome_options.add_argument('--window-size=1920x1080')  # Set the window size

    # Desired capabilities for BrowserStack
    chrome_options.set_capability('browserName', 'Chrome')
    chrome_options.set_capability('browserVersion', 'latest')
    chrome_options.set_capability('bstack:options', {
        'os': 'Windows',
        'osVersion': '10',
        'local': 'false',
        'seleniumVersion': '4.0.0',
        'userName': BROWSERSTACK_USERNAME,
        'accessKey': BROWSERSTACK_ACCESS_KEY,
        # Removed 'name' as it causes schema errors
    })

    # Initialize the remote WebDriver with BrowserStack URL and options
    driver = webdriver.Remote(
        command_executor=BROWSERSTACK_URL,
        options=chrome_options
    )

    """
    
    INSANE

    """
    driver.implicitly_wait(15)  # Set implicit wait for 15 seconds
    print("Driver created successfully!")  # Debugging print
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
    
def save_location_to_retry_file(location, retry_filename='retry.json'):
    """Saves a location object to the retry file if max retries are reached."""
    with open(retry_filename, 'a', encoding='utf-8') as retry_file:
        json.dump(location, retry_file, ensure_ascii=False)
        retry_file.write('\n')

def scrape_location(location, max_retries=3):
    retry_count = 0
    
    while retry_count < max_retries:
        driver = create_driver()
        try:
            location_id = location['id']
            geolocation = location['geolocation']
            
            base_url = "https://www.index.hr/oglasi/nekretnine/prodaja-stanova/pretraga?searchQuery=%257B%2522category%2522%253A%2522prodaja-stanova%2522%252C%2522module%2522%253A%2522nekretnine%2522%252C%2522includeSettlementIds%2522%253A%255B%2522{location_id}%2522%255D%252C%2522sortOption%2522%253A4%257D"
            url = base_url.format(location_id=location_id)
            driver.get(url)
            
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "headerDesktop__searchResult___1uh7t"))
            )

            all_ads = []

            page = 1
            
            ad_count_element = driver.find_element(By.CLASS_NAME, "headerDesktop__searchResult___1uh7t")
            ad_count_number = ad_count_element.find_element(By.TAG_NAME, "span").text
            ad_count = ad_count_number.split(" ")[1]
            
            print(ad_count)
            if not ("." in ad_count) and int(ad_count) == 0:
                print("No ads found, quitting.")
                driver.quit()
                return []

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".AdLink__link___3Iz86"))
            )

            while True:
                ads = driver.find_elements(By.CSS_SELECTOR, ".AdLink__link___3Iz86")
                if not ads:
                    break

                for ad in ads:
                    date = safe_find_text(ad, ".AdSummary__info___2tUOv span")
                    title = ad.get_attribute("title") if ad.get_attribute("title") else "N/A"
                    price_text = safe_find_text(ad, ".adPrice__price___3o3Dk")
                    
                    if "-" in price_text:
                        price_text = price_text.split("-")[0]
                    try:
                        price = int(price_text.replace('.', '').replace('€', '').strip()) if price_text != "N/A" else "N/A"
                    except:
                        price = float(price_text.replace('€', '').replace(".", "").replace(",", ".").strip())
                        price = int(price)
                    dimensions = safe_find_text(ad, ".style__value___37YPR")
                    room_type = "N/A"
                    auction_url = ad.get_attribute("href") if ad.get_attribute("href") else "N/A"
                    
                    all_ads.append({
                        "date": date,
                        "title": title,
                        "price": price,
                        "dimensions": dimensions,
                        "room_type": room_type,
                        "location": location['name'],
                        "geolocation": geolocation,
                        "url": auction_url,
                        "lvl3-poly": location['lvl3-poly']
                    })

                if not ("." in ad_count):
                    if(int(ad_count) > 24):
                        # Check if the next button is disabled
                        next_button = driver.find_element(By.CSS_SELECTOR, "li.ant-pagination-next")
                        if 'ant-pagination-disabled' in next_button.get_attribute('class'):
                            print("disabled ", page)
                            break  # Exit loop if the next button is disabled
                        next_button.click()
                    else:
                        break
                else:
                    next_button = driver.find_element(By.CSS_SELECTOR, "li.ant-pagination-next")
                    if 'ant-pagination-disabled' in next_button.get_attribute('class'):
                        print("disabled ", page)
                        break  # Exit loop if the next button is disabled
                    next_button.click()


            return all_ads

        except StaleElementReferenceException as e:
            retry_count += 1
            print(f"StaleElementReferenceException encountered for location {location['name']}. Retry {retry_count}/{max_retries}.")
            driver.quit()
            time.sleep(2)  # Optional: Wait a bit before retrying

        except Exception as e:
            retry_count += 1
            print(f"Error processing location {location['name']}: {e}")
            log_error_to_file('error_log.txt', f"Error processing location {location['name']}: {e}")
            driver.quit()
            time.sleep(2)

    if retry_count == max_retries:
        save_location_to_retry_file(location) 
        print(f"Failed to process location {location['name']} after {max_retries} retries. Skipping.")
        log_error_to_file('error_log.txt', f"Failed to process location {location['name']} after {max_retries}.")
        driver.quit()  # Ensure driver is quit if max retries are reached
    
    return []

def log_error_to_file(file_path, message):
    """Appends an error message to a log file."""
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(message + '\n')
        
        
# Main function to manage parallel scraping
# Main function to manage parallel scraping
def main():
    global data
    data = []
    batch_size = 0
    save_interval = 10  # Adjust this to control the number of locations before saving
   
    with open('w11-lenfixed-stan.json', 'r', encoding='utf-8') as f: #w11-lenfixed-stan
        locations = json.load(f)
    
    # Use ThreadPoolExecutor to manage parallel execution of scraping
    with ThreadPoolExecutor(max_workers=3) as executor:  # Consider lowering max_workers
        futures = {executor.submit(scrape_location, location): location for location in locations}

        for i, future in enumerate(as_completed(futures), start=1):
            
            location_data = future.result()
            data.extend(location_data)
            batch_size += 1                
            append_to_json_lines_file('STANOVI-18-10.json', data)
            print(f"Data saved after processing {batch_size} locations.")
            data = []  # Clear data to free memory
                

            #except Exception as e:
                #error_message = f"Error processing location {futures[future]['name']}: {e}"
                #log_error_to_file('error_log.txt', error_message)

        # Input and output file paths
    input_file_path = 'retry.json'  # Replace this with your input file path
    output_file_path = 'retry-fixed.json'  # Output file path for the fixed JSON

    # Read the broken JSON file and process each line
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        json_objects = []
        for line in infile:
            line = line.strip()  # Remove any extra whitespace
            if line:  # Ensure the line is not empty
                try:
                    # Try to load each line as a JSON object to make sure it's valid
                    json_obj = json.loads(line)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    # Handle partially broken JSON objects (you can modify as needed)
                    print(f"Warning: Skipping invalid JSON object: {line}")

    # Write the fixed JSON to the output file in a proper JSON array format
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        json.dump(json_objects, outfile, indent=4)
        
    
    with open('retry-fixed.json', 'r', encoding='utf-8') as f: #w11-lenfixed-stan
        locations = json.load(f)
                
    with ThreadPoolExecutor(max_workers=1) as executor:  # Consider lowering max_workers
        futures = {executor.submit(scrape_location, location): location for location in locations}

        for i, future in enumerate(as_completed(futures), start=1):
            
            location_data = future.result()
            data.extend(location_data)
            batch_size += 1                
            append_to_json_lines_file('STANOVI-18-10.json', data)
            print(f"Data saved after processing {batch_size} locations.")
            data = []  # Clear data to free memory

if __name__ == "__main__":
    main()
