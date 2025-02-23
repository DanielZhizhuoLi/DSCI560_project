import os
import re
import json
import pandas as pd

# Define the expected keys
MAIN_KEYS = [
    "Date Stimulated", "Stimulated Formation", "Top (Ft)", 
    "Bottom (Ft)", "Stimulation Stages", "Volume", "Volume Units"
]
TYPE_KEYS = [
    "Type Treatment", "Acid %", "Lbs Proppant", 
    "Maximum Treatment Pressure (PSI)", "Maximum Treatment Rate (BBLS/Min)"
]

def clean_text(text):
    """
    Cleans up text by removing excessive spaces, newlines, and special characters.
    """
    return re.sub(r'\s+', ' ', text).strip()

def extract_values_using_regex(text, keys):
    """
    Uses regex to dynamically extract values corresponding to given keys.
    """
    extracted_data = {key: None for key in keys}  # Initialize with None
    
    # Extract values by matching key-value patterns
    for key in keys:
        pattern = rf"{re.escape(key)}\s*[:|-]?\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data[key] = clean_text(match.group(1))

    return extracted_data

def parse_blocks(cell_text):
    """
    Parses the text block to extract the main stimulation data and type treatment.
    """
    lower_text = cell_text.lower()

    # Check for the main stimulation table
    if "date stimulated" in lower_text or "stimulated formation" in lower_text:
        return extract_values_using_regex(cell_text, MAIN_KEYS)

    # Check for the type treatment section
    elif "type treatment" in lower_text:
        extracted_data = extract_values_using_regex(cell_text, TYPE_KEYS)

        # Extract details separately (lines after "Details" keyword)
        details_match = re.search(r"Details\s*[:|-]?\s*(.+)", cell_text, re.IGNORECASE)
        extracted_data["Details"] = clean_text(details_match.group(1)) if details_match else ""

        return extracted_data
    
    return {}

def read_csv_as_text_blocks(csv_path):
    """
    Reads a CSV file and extracts each row as a block of text.
    """
    df = pd.read_csv(csv_path, header=None, dtype=str)
    cells = []

    for row in df.itertuples(index=False):
        cell_text = " ".join(str(x) for x in row if pd.notna(x)).strip()
        if cell_text:
            cells.append(cell_text)

    return cells

def parse_csv_to_json(csv_path):
    """
    Reads a CSV file, extracts data, and returns structured JSON.
    """
    cells = read_csv_as_text_blocks(csv_path)
    merged_record = {}

    for cell in cells:
        cell_data = parse_blocks(cell)
        print("Extracted:", cell_data)
        merged_record.update(cell_data)

    return merged_record

def process_all_csv(csv_dir, output_json_path):
    """
    Processes all CSV files and saves structured data in JSON.
    """
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]

    if not csv_files:
        print("No CSV files found.")
        return

    merged_data = {}

    for csv_file in csv_files:
        csv_path = os.path.join(csv_dir, csv_file)
        print(f"Processing File: {csv_path}")
        structured_data = parse_csv_to_json(csv_path)
        key_name = os.path.splitext(csv_file)[0]
        merged_data[key_name] = structured_data

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"Merged JSON saved to {output_json_path}")

def main():
    csv_dir = "../data/csv"  # Directory containing CSVs
    output_json = "../data/json_output/merged_stimulation.json"
    process_all_csv(csv_dir, output_json)

if __name__ == "__main__":
    main()
