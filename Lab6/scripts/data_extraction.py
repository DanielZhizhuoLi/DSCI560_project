import re
from collections import Counter

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
	return well_name, api

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

def extract_stimulation_data(txt):
	txt = txt.replace("!", "|").replace("\n", " ").strip()
	header_pattern = re.compile(r"""
        Date\s+Stimulated\s*\|?\s*Stimulated\s+Formation\s*\|?\s*Top\s*\(Ft\)\s*\|?\s*Bottom\s*\(Ft\)\s*\|?
        Stimulation\s+Stages\s*\|?\s*Volume\s*\|?\s*Volume\s+Units\s*\|?\s*Type\s+Treatment\s*\|?\s*Acid\s*%\s*\|?
        Lbs\s+Proppant\s*\|?\s*Maximum\s+Treatment\s+Pressure\s*\(PSI\)\s*\|?\s*Maximum\s+Treatment\s+Rate\s*\(BBLS/Min\)
    """, re.VERBOSE)

    	# Check if the header exists in the document
	if not re.search(header_pattern, txt):
		print("No matching column headers found. Skipping table extraction.")
		return []
	table_pattern = re.compile(r"""
        (\d{2}/\d{2}/\d{4})                # Date
        \s+([A-Za-z\s\d]+)                 # Stimulated Formation
        \s*(\d*)                           # Top (optional)
        \s*(\d*)                           # Bottom (optional)
        \s*(\d*)                           # Stimulation Stages (optional)
        \s*(\d*)                           # Volume (optional)
        \s*([A-Za-z]+)?                    # Volume Units (optional)
        \s*([A-Za-z\s]+)?                  # Type Treatment (optional)
        \s*(\d*)                           # Acid % (optional)
        \s*(\d*)                           # Lbs Proppant (optional)
        \s*(\d+(\.\d+)?)?                  # Maximum Treatment Pressure (optional)
        \s*(\d+(\.\d+)?)?                  # Maximum Treatment Rate (optional)
        \s*([\w\s#\-,\.]*)?                # Details (optional, multiline)
	""", re.VERBOSE)
	table_rows = table_pattern.findall(txt)
	if not table_rows:
		print("No table row found")
	stimulation_data = []
	for row in table_rows:
		stimulation_row = {
		"Date Stimulated": row[1] if len(row) > 1 and row[1] else None,
		"Stimulated Formation": row[2] if len(row) > 2 and row[2] else None,
		"Top (Ft)": row[3] if len(row) > 3 and row[3] else None,
		"Bottom (Ft)": row[4] if len(row) > 4 and row[4] else None,
		"Stimulation Stages": row[5] if len(row) > 5 and row[5] else None,
		"Volume": row[6] if len(row) > 6 and row[6] else None,
		"Volume Units": row[7] if len(row) > 7 and row[7] else None,
		"Type Treatment": row[8] if len(row) > 8 and row[8] else None,
		"Acid %": row[9] if len(row) > 9 and row[9] else None,
		"Lbs Proppant": row[10] if len(row) > 10 and row[10] else None,
		"Maximum Treatment Pressure (PSI)": row[11] if len(row) > 11 and row[11] else None,
		"Maximum Treatment Rate (BBLS/Min)": row[12] if len(row) > 12 and row[12] else None,
		"Details": row[13] if len(row) > 13 and row[13] else None
		}
		stimulation_data.append(stimulation_row)
	return stimulation_data


with open("../data/extracted_data/ocr_W25159.txt", 'r', encoding='utf-8') as f:
	text = f.read()

	well_name, api = extract_well_info(text)
	tables = extract_stimulation_data(text)
	print(well_name)
	print(api)
	for table in tables:
		print(table)
