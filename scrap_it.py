from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
import requests

app = Flask(__name__)

def extract_coordinates(map_url):
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get(map_url)

    time.sleep(5)

    current_url = driver.current_url
    driver.quit()

    match = re.search(r'@([0-9\.-]+),([0-9\.-]+)', current_url)
    if match:
        lat = float(match.group(1))
        lng = float(match.group(2))
        return lat, lng
    return None, None

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

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
