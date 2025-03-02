import os
import pdfplumber
import camelot

def filter_stimulation_pages(pdf_path, keywords=None):
    """
    Returns a list of page numbers where any of the given keywords appear.
    """
    if keywords is None:
        # Default to "Well Specific Stimulation" plus some variations
        keywords = ["Well Specific Stimulation", "Stimulation Data", "Stimulated Formation"]
    
    matched_pages = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            # Lowercase to do case-insensitive matching
            page_text_lower = text.lower()
            
            # If any keyword is found in this page's text, record the page number
            if any(k.lower() in page_text_lower for k in keywords):
                matched_pages.append(page_num)
    
    return matched_pages

def extract_stimulation_table(pdf_path, pages, flavor="stream"):
    """
    Uses Camelot to extract tables from only the specified pages.
    Returns a list of tables.
    """
    # Convert the pages list into a comma-separated string for Camelot
    pages_str = ",".join(map(str, pages))
    
    tables = camelot.read_pdf(pdf_path, pages=pages_str, flavor="stream",
        row_tol=10,         
        column_tol=10,     
        edge_tol=50,        
        strip_text='\n', debug=True)
    
    return tables

def main():
    pdf_file = "../data/processed_data/ocr_W20407.pdf"  # ocr_W20407.pdf, ocr_W22221
    
    # 1. Find pages with stimulation-related keywords
    pages_with_stimulation = filter_stimulation_pages(pdf_file, keywords=[
        "Well Specific Stimulation",
        "Stimulation Data",
        "Stimulated Formation",
        "Proppant",
        "Maximum Treatment Pressure"
    ])
    print("Pages containing stimulation info:", pages_with_stimulation)
    
    if not pages_with_stimulation:
        print("No pages found with stimulation keywords.")
        return
    
    # 2. Extract tables on those pages using Camelot
    tables = extract_stimulation_table(pdf_file, pages_with_stimulation, flavor="stream")
    print(f"Detected {tables.n} tables in the matched pages.")
    
    # 3. Specify the output directory and create it if needed
    output_dir = "../data/csv_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory {output_dir}")
    else:
        print(f"Output directory {output_dir} exists.")
    
    # 4. Display or save each table to the specified directory
    for i, table in enumerate(tables):
        df = table.df  # Convert to Pandas DataFrame
        print(f"--- Table {i} (page {table.page}) ---")
        print(df)
        
        # Save the DataFrame to a CSV file in the output directory
        output_csv = os.path.join(output_dir, f"stimulation_page_{table.page}_idx_{i}.csv")
        df.to_csv(output_csv, index=False)
        print(f"Saved to {output_csv}")

if __name__ == "__main__":
    main()
