import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import json
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

with open('../station_codes.csv') as f:
    text = f.read()
text = text.replace('\n', ',')
print(text)
result = text.split(',')
print(result)
codes = []
for i in range(len(result)):
    if result[i].isupper() and len(result[i]) == 3:
        codes.append(result[i])
print(codes)
# Establish chrome driver and go to report site URL
url = "https://www.brtimes.com/!home"
driver = webdriver.Safari()
contimes = dict()

for station in codes:
    driver.get(url)
    stationBox = driver.find_element(By.ID, 'station')
    stationBox.send_keys(station)
    stationBox.send_keys(Keys.RETURN)
    time.sleep(0.5)
    try:
        elem = driver.find_element(By.XPATH, ('/html/body/div[6]/div[2]/div[1]'))
    except selenium.common.exceptions.NoSuchElementException:
        contimes[station] = 'No data'
        continue
    number = [s for s in elem.text.split() if s.isdigit()]
    print(station + ', ' + number[0])
    contimes[station] = number[0]
    time.sleep(0.2)

f = open('../contimes.json', 'w')
json.dump(contimes, f)