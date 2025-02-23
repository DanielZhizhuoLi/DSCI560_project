import re
from collections import Counter
import os
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import time
import json



def extract_well_info(txt):
	api_pattern = re.compile(r'\b\d{2}-\d{3}-\d{5}\b')
	well_name_pattern = re.compile(r"Well Name and Number[^\n]*\n([A-Za-z0-9\s&-]+)")
	api_match = api_pattern.findall(txt)
	api_count = Counter(api_match)
	api = api_count.most_common(1)[0][0] if api_count else "Not Found"

	well_match = well_name_pattern.findall(txt)
	if well_match:
		well_name = find_most_common_substring(well_match)
	else:
		well_name = 'Not Found'
	cleaned_name = re.split(r"\s*Before\s*", well_name, maxsplit=1)[0]
	return cleaned_name, api

def find_most_common_substring(well_names):
	all_substrings = []
	for name in well_names:
		words = name.split()
		substring = [" ".join(words[:i]) for i in range(1, len(words)+1)]
		all_substrings.extend(substring)
	substrings_count = Counter(all_substrings)
	sorted_substrings = sorted(substrings_count.items(), key=lambda x: (-x[1], -len(x[0])))
	most_common_substring = sorted_substrings[0][0] if sorted_substrings else "Not Found"
	return most_common_substring


DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "well"

def scrape_well_data(well_name, api):
	service = Service("/home/tsung-ting-lee/Downloads/chromedriver-linux64/chromedriver")
	driver = webdriver.Chrome(service=service)
	data = {
	"block_stats": [],
	"well_status": None,
	"well_type": None,
	"closest_city": None
	 }
	try:
		url = "https://www.drillingedge.com/search"
		driver.get(url)
		time.sleep(2)
		# found the column and input well name
		well_input = driver.find_element(By.NAME, "well_name")
		well_input.send_keys(well_name)

		# found the column and input api
		api_input = driver.find_element(By.NAME, "api_no")
		api_input.send_keys(api)

		api_input.send_keys(Keys.RETURN)

		try:
			# Wait for the results
			WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_wrapper")))
			table = driver.find_element(By.CSS_SELECTOR, "div.table_wrapper table.table.wide-table.interest_table")
			link_element = table.find_element(By.TAG_NAME, "a")
			href = link_element.get_attribute("href")


			# direct to the new page
			driver.get(href)
			WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
			data = {}

			block_stats = driver.find_elements(By.CLASS_NAME, "block_stat")
			data["block_stats"] = []
			for block_stat in block_stats:
				try:
					number = block_stat.find_element(By.CLASS_NAME, "dropcap").text
					content = block_stat.text.replace(number, "").strip()
					data["block_stats"].append({
						"number": number,
						"content": content})
				except:
					print("block stats not found")
				try:
					well_status = driver.find_element(By.XPATH, "//th[contains(text(), 'Well Status')]/following-sibling::td").text
					data["well_status"] = well_status
				except:
					print("Well status not found.")
				try:
					well_type = driver.find_element(By.XPATH, "//th[contains(text(), 'Well Type')]/following-sibling::td").text
					data["well_type"] = well_type
				except:
					print("Well type not found.")
				try:
					closest_city = driver.find_element(By.XPATH, "//th[contains(text(), 'Closest City')]/following-sibling::td").text
					data["closest_city"] = closest_city
				except:
					print("Closest city not found.")
		except TimeoutException:
			print(f"No result for {well_name} and {api}")
			return data
	except Exception as e:
		print(f"an error occur: {e}")
		return data
	finally:
		driver.quit()
	print(data)
	return data

def connect_db():
	return pymysql.connect(host = DB_HOST, user= DB_USER, password=DB_PASSWORD, database=DB_NAME)

def check_duplicates(cursor, well_name, api):
    sql = "SELECT * FROM well WHERE name = %s AND api = %s"
    cursor.execute(sql, (well_name, api))
    return cursor.fetchone() is not None


def insert_data(data):
	conn = connect_db()
	cursor = conn.cursor()
	cursor.execute('''
    CREATE TABLE IF NOT EXISTS well (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(30),
	API CHAR(12),
	block_stats JSON,
	well_status VARCHAR(10),
	well_type VARCHAR(20),
	closest_city VARCHAR(30),
	filename VARCHAR(6) 
	);
	''')

	for record in data:
		well_name = record.get("well_name")
		api = record.get("api")
		block_stats = json.dumps(record.get("block_stats"))
		well_status = record.get("well_status")
		well_type = record.get("well_type")
		closest_city = record.get("closest_city")
		filename = record.get("filename")
		if not check_duplicates(cursor, well_name, api):
			sql = """INSERT INTO well (name, API, block_stats, well_status, well_type, closest_city, filename)
				VALUE(%s, %s, %s, %s, %s, %s, %s)"""
			values = (well_name, api, block_stats, well_status, well_type, closest_city, filename)
			cursor.execute(sql, values)
			print(f"insert record")
		else:
			print("duplicated record")
	conn.commit()
	cursor.close()
	conn.close()
	print(f"Data saved successfully")

data = []
input_folder = "../data/extracted_data"
for filename in os.listdir(input_folder):
	input_path = os.path.join(input_folder, filename)
	with open(input_path, 'r', encoding='utf-8') as f:
		text = f.read()

		well_name, api = extract_well_info(text)
		print(well_name)
		print(api)

		scraped_data = scrape_well_data(well_name, api)
		output_filename = os.path.split(filename)[0]
		record = {
			"well_name": well_name,
			"api": api,
			"filename": output_filename,
			**scraped_data}
		data.append(record)

insert_data(data)
