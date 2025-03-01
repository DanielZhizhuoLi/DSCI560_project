import re
from collections import Counter
import os
import pymysql
import csv


input_folder = "../data/extracted_data"
output_folder = "../data/stimulation_data"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def extract_stimulation_text(text):
    start_index = text.find("Date Stimulated")
    if start_index == -1:
        return None  # Return None if the keyword is not found
    
    # Extract the next 10 lines starting from the match
    lines = text[start_index:].splitlines()  # Split text into lines
    extracted_lines = lines[:11]  # Get the first 11 lines (including the match line)
    extracted_text = "\n".join(extracted_lines)  # Join lines back into a single string
    
    return extracted_text

def store_stimulation_text():
	for filename in os.listdir(input_folder):
		input_path = os.path.join(input_folder, filename)
		
		# Read the text file
		with open(input_path, 'r', encoding='utf-8') as f:
			text = f.read()
		
		# Extract stimulation data
		extracted_text = extract_stimulation_text(text)
		
		if extracted_text:
			# Save the extracted text to a new file in the output folder
			output_filename = f"stimulation_{filename}"
			output_path = os.path.join(output_folder, output_filename)
			
			with open(output_path, 'w', encoding='utf-8') as f:
				f.write(extracted_text)
			print(f"Extracted data saved to {output_filename}")
		else:
			print(f"No stimulation data found in {filename}")


def extract_stimulation_data(txt, filename):
    # Define a pattern for the main stimulation table
    stimulation_pattern = re.compile(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+"  # Date (e.g., 03/29/2015, May 16, 2015)
        r"([\w\s]+?)\s+"  # Stimulated Formation (e.g., Three Forks)
        r"(\d+)\s+"  # Top (Ft)
        r"(\d+)\s+"  # Bottom (Ft)
        r"(\d+)\s+"  # Stimulation Stages
        r"(\d+)\s+"  # Volume
        r"([A-Za-z]+)"  # Volume Units (e.g., Barrels)
    )
    
    # Define a pattern for the treatment details
    treatment_pattern = re.compile(
        r"Type Treatment\s+IAcid %\s+ILbs Proppant\s+Maximum Treatment Pressure \(PSI\)\s+Maximum Treatment Rate \(BBLS/Min\)\s*"
        r"([\w\s]+?)\s+"  # Type Treatment (e.g., Sand Frac)
        r"(\d*\.?\d*)\s+"  # Acid % (optional, can be empty)
        r"(\d+)\s+"  # Lbs Proppant
        r"(\d+)\s+"  # Maximum Treatment Pressure (PSI)
        r"(\d+\.?\d*)"  # Maximum Treatment Rate (BBLS/Min)
    )
    
    # Define a pattern for the Details section
    details_pattern = re.compile(
        r"Details\s+(.*?)(?=\nDate Stimulated|\nType Treatment|\Z)", re.DOTALL
    )
    
    # Find all matches in the text
    stimulation_matches = stimulation_pattern.findall(txt)
    treatment_matches = treatment_pattern.findall(txt)
    details_matches = details_pattern.findall(txt)
    
    print(f"Found {len(stimulation_matches)} stimulation matches in {filename}")
    print(f"Found {len(treatment_matches)} treatment matches in {filename}")
    print(f"Found {len(details_matches)} details matches in {filename}")
    
    # Create a list of extracted data from the matches
    extracted_data = []
    for i in range(len(stimulation_matches)):
        data_dict = {
            "Filename": filename,  # Add the filename to the record
            "Date Stimulated": stimulation_matches[i][0],
            "Stimulated Formation": stimulation_matches[i][1].strip(),
            "Top (Ft)": stimulation_matches[i][2],
            "Bottom (Ft)": stimulation_matches[i][3],
            "Stimulation Stages": stimulation_matches[i][4],
            "Volume": stimulation_matches[i][5],
            "Volume Units": stimulation_matches[i][6],
            "Type Treatment": treatment_matches[i][0] if i < len(treatment_matches) else "",
            "Acid %": treatment_matches[i][1] if i < len(treatment_matches) else "",
            "Lbs Proppant": treatment_matches[i][2] if i < len(treatment_matches) else "",
            "Maximum Treatment Pressure (PSI)": treatment_matches[i][3] if i < len(treatment_matches) else "",
            "Maximum Treatment Rate (BBLS/Min)": treatment_matches[i][4] if i < len(treatment_matches) else "",
            "Details": details_matches[i].strip() if i < len(details_matches) else ""
        }
        extracted_data.append(data_dict)
    
    return extracted_data

DB_HOST = "localhost"
DB_USER = "phpmyadmin"
DB_PASSWORD = "StrongPassw0rd123!"
DB_NAME = "well"

def connect_db():
	return pymysql.connect(host = DB_HOST, user= DB_USER, password=DB_PASSWORD, database=DB_NAME)

def check_duplicates(cursor, filename):
    sql = "SELECT * FROM stimulation WHERE filename = %s"
    cursor.execute(sql, (filename,))
    return cursor.fetchone() is not None


def insert_data(data):
	conn = connect_db()
	cursor = conn.cursor()
	cursor.execute('''
    CREATE TABLE IF NOT EXISTS stimulation (
        id INT AUTO_INCREMENT PRIMARY KEY,
		date_stimulated VARCHAR(10),
		stimulated_formation VARCHAR(20),
		top_ft INT,
		bottom_ft INT,
		stimulation_stages INT,
		volume INT,
		volume_units VARCHAR(20),
		type_treatment VARCHAR(50),
		acid_percent DECIMAL(5, 2),
		lbs_proppant INT,
		max_treatment_pressure INT,
		max_treatment_rate DECIMAL(10, 2),
		details TEXT,
		filename VARCHAR(10) 
	);
	''')

	for record in data:
		date_stimulated = record.get("Date Stimulated")
		stimulated_formation = record.get("Stimulated Formation")
		top_ft = record.get("Top (Ft)")
		bottom_ft = record.get("Bottom (Ft)")
		stimulation_stages = record.get("Stimulation Stages")
		volume = record.get("Volume")
		volume_units = record.get("Volume Units")
		type_treatment = record.get("Type Treatment")
		acid_percent = record.get("Acid %")
		lbs_proppant = record.get("Lbs Proppant")
		max_treatment_pressure = record.get("Maximum Treatment Pressure (PSI)")
		max_treatment_rate = record.get("Maximum Treatment Rate (BBLS/Min)")
		details = record.get("Details")
		filename = record.get("Filename")

		# there will be error if integer or decimal is ""
		if top_ft == "":
				top_ft = None
		if bottom_ft == "":
				bottom_ft = None
		if stimulation_stages == "":
				stimulation_stages = None
		if volume == "":
				volume = None
		if acid_percent == "":
				acid_percent = None
		if lbs_proppant == "":
				lbs_proppant = None
		if max_treatment_pressure == "":
				max_treatment_pressure = None
		if max_treatment_rate == "":
				max_treatment_rate = None

		if not check_duplicates(cursor, filename):
			sql = """
				INSERT INTO stimulation (
					date_stimulated, stimulated_formation, top_ft, bottom_ft, stimulation_stages, 
					volume, volume_units, type_treatment, acid_percent, lbs_proppant, 
					max_treatment_pressure, max_treatment_rate, details, filename
				)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
			"""
			values = (
				date_stimulated, stimulated_formation, top_ft, bottom_ft,
				stimulation_stages, volume, volume_units, type_treatment, acid_percent,
				lbs_proppant, max_treatment_pressure, max_treatment_rate, details, filename
			)
			cursor.execute(sql, values)
			print(f"Inserted record for filename: {filename}")
		else:
			print(f"Duplicate record for filename: {filename}")

	conn.commit()
	cursor.close()
	conn.close()
	print("Data saved successfully")

all_extracted_data = []
input_folder = "../data/stimulation_data"
for filename in os.listdir(input_folder):
	input_path = os.path.join(input_folder, filename)
	output_filename = os.path.splitext(filename)[0].split("_")[-1] 
	with open(input_path, 'r', encoding='utf-8') as f:
		text = f.read()
		extracted_data = extract_stimulation_data(text, output_filename)
		all_extracted_data.extend(extracted_data)
with open("../data/stimulation_data.csv", mode='w', newline="", encoding="utf-8") as file:
	writer = csv.DictWriter(file, fieldnames= all_extracted_data[0].keys())
	writer.writeheader()
	writer.writerows(all_extracted_data)


insert_data(all_extracted_data)
