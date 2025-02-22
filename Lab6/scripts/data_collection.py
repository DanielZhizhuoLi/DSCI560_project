import pymysql
import pandas as pd
import pdfplumber
import os
import ocrmypdf


def ocr_transform():
	input_folder = "../data/raw_data"
	output_folder = "../data/ocr_data"
	os.makedirs(output_folder, exist_ok=True)
	for filename in os.listdir(input_folder):
		if filename.endswith(".pdf"):
			output_filename = "ocr_" + filename
			input_pdf = os.path.join(input_folder, filename)
			output_pdf = os.path.join(output_folder, output_filename)
			print(f"Processing: {filename}...")
			try:
				ocrmypdf.ocr(
					input_pdf,
					output_pdf,
					deskew=True,
					clean=True,
				 	skip_text=True,
				 	jobs=1)
				print(f"Successfully processed: {filename}")
			except Exception as e:
				print(f"error processing {filename}:  {e}")
	print("all pdfs processed")

def keyword_extract():
	input_folder = "../data/ocr_data"
	output_folder = "../data/extracted_data"
	os.makedirs(output_folder, exist_ok=True)

	keywords= ["WELL INFORMATION","Well Information", "Well Name", "API", "LONGITUDE", "longitude", "Stimulated", "Latitude", "LATITUDE"] 
	for filename in os.listdir(input_folder):
		input_path = os.path.join(input_folder, filename)
		txt_filename = filename.replace(".pdf", ".txt")
		output_path = os.path.join(output_folder, txt_filename)
		extracted_text = [] 
		with pdfplumber.open(input_path) as file:
			for page_num, page in enumerate(file.pages):
				text = page.extract_text()
				if  text  and any(keyword in text for keyword in keywords):
					print(f"Found stimulation text on page {page_num +1} in {filename}")
					extracted_text.append(text)
		print(extracted_text)
		with open(output_path, "w", encoding='utf-8') as f:
			f.write("\n".join(extracted_text))
		print(f"Extracted text saved to : {output_path}")
	print(f"\nProcessed PDFs containing target keywords.")
keyword_extract()
