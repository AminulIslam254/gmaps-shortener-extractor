from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests

app = Flask(__name__)

def extract_coordinates(map_url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222") 
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(map_url)

        WebDriverWait(driver, 10).until(lambda d: '@' in d.current_url)

        current_url = driver.current_url
        print(f"[DEBUG] Current redirected URL: {current_url}")

        match = re.search(r'@([0-9\.-]+),([0-9\.-]+)', current_url)
        if match:
            lat = float(match.group(1))
            lng = float(match.group(2))
            return lat, lng
    except Exception as e:
        print(f"[ERROR] Failed to extract coordinates: {e}")
    finally:
        if driver:
            driver.quit()

    return None, None


@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome! The Flask server is running."})

@app.route('/get-coordinates', methods=['POST'])
def get_coordinates():
    data = request.get_json()
    map_url = data.get('url')
    print(f"hit got data {map_url}")

    if not map_url:
        return jsonify({"error": "Missing 'url' in request"}), 400

    response = requests.get(map_url, allow_redirects=True)
    long_url = response.url

    lat, lng = extract_coordinates(long_url)

    if lat and lng:
        return jsonify({"latitude": lat, "longitude": lng})
    else:
        return jsonify({"error": "Could not extract coordinates"}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
