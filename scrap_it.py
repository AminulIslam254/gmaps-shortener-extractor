from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import re
import requests

app = Flask(__name__)


options = Options()
options.add_argument("--headless=new") 
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--remote-debugging-port=9222") 

options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
options.add_argument("--blink-settings=imagesEnabled=false")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-background-timer-throttling")
options.add_argument("--disable-backgrounding-occluded-windows")
options.add_argument("--disable-renderer-backgrounding")
options.add_argument("--disable-client-side-phishing-detection")
options.add_argument("--disable-default-apps")
options.add_argument("--no-first-run")
options.add_argument("--no-zygote")

options.add_argument("--window-size=800,600")

driver = webdriver.Chrome(options=options)



def extract_coordinates(map_url):
    try:
        driver.get(map_url)

        while '@' not in driver.current_url:
            time.sleep(0.1)

        current_url = driver.current_url
        print(f"[DEBUG] Current redirected URL: {current_url}")

        match = re.search(r'@([0-9\.-]+),([0-9\.-]+)', current_url)
        if match:
            lat = float(match.group(1))
            lng = float(match.group(2))
            return lat, lng
    except Exception as e:
        print(f"[ERROR] Failed to extract coordinates: {e}")

    return None, None



def scrape_places(map_search_url):
    try:
        driver.get(map_search_url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.Nv2PK.Q2HXcd.THOPZb")))

        places = []

        results = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK.Q2HXcd.THOPZb")

        for r in results[:5]:
            try:
                name = r.find_element(By.CSS_SELECTOR, "div.qBF1Pd.fontHeadlineSmall").text
            except:
                name = None
    
            try:
                place_link = r.find_element(By.CSS_SELECTOR, "a.hfpxzc").get_attribute("href")
                match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', place_link)
                if match:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                else:
                    lat, lng = None, None
            except:
                lat, lng = None, None

            places.append({
                "name": name,
                "latitude": lat,
                "longitude": lng
            })

        return places

    except Exception as e:
        print(f"[ERROR] scraping places failed: {e}")
        return []
    



@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome! The Flask server is running."})

@app.route('/get-coordinates', methods=['POST'])
def get_coordinates():
    data = request.get_json()
    map_url = data.get('url')

    if not map_url:
        return jsonify({"error": "Missing 'url' in request"}), 400

    response = requests.get(map_url, allow_redirects=True)
    long_url = response.url

    lat, lng = extract_coordinates(long_url)

    if lat and lng:
        return jsonify({"latitude": lat, "longitude": lng})
    else:
        return jsonify({"error": "Could not extract coordinates"}), 500

@app.route('/scrape-places', methods=['POST'])
def scrape_places_route():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' in request"}), 400

    places = scrape_places(url)
    if places:
        return jsonify({"places": places})
    else:
        return jsonify({"error": "No places found or scraping failed"}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
