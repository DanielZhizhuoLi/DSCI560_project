import os
import pdfplumber
import camelot

def filter_stimulation_pages(pdf_path, keywords=None):

    if keywords is None:
        keywords = ["Well Specific Stimulation", "Stimulation Data", "Stimulated Formation"]
    
    matched_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if any(k.lower() in text.lower() for k in keywords):
                matched_pages.append(page_num)
    return matched_pages

def extract_stimulation_table(pdf_path, pages, flavor="stream"):

    pages_str = ",".join(map(str, pages))
    tables = camelot.read_pdf(pdf_path, pages=pages_str, flavor="stream",
        row_tol=10,          # 可尝试 5, 10, 15 等
        column_tol=10,       # 同上，根据实际效果微调
        edge_tol=50,         # 如果文本有较大空白区域，可加大该值
        strip_text='\n', debug=True)
    return tables

def process_pdf(pdf_path, output_dir):

    print(f"dealing : {pdf_path}")
    pages_with_stimulation = filter_stimulation_pages(pdf_path, keywords=[
        "Well Specific Stimulation",
        "Stimulation Data",
        "Stimulated Formation",
        "Proppant",
        "Maximum Treatment Pressure"
    ])
    print(":", pages_with_stimulation)
    if not pages_with_stimulation:
        print("no stimulation data")
        return


    tables = extract_stimulation_table(pdf_path, pages_with_stimulation, flavor="stream")
    print(f"在匹配页面中检测到 {tables.n} 个表格。")
    

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    

    for idx, table in enumerate(tables, start=1):
        df = table.df  # 转换为 Pandas DataFrame
        print(f"--- {pdf_name} 表格 {idx} (页面 {table.page}) ---")
        print(df)
        
        output_csv = os.path.join(output_dir, f"{pdf_name}_{idx}.csv")
        df.to_csv(output_csv, index=False)
        print(f"已保存到 {output_csv}")

def main():
    # PDF 文件所在目录
    pdf_dir = "../data/processed_data"
    # CSV 输出目录
    output_dir = "../data/csv"
    
    # 如果输出目录不存在，则创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")
    else:
        print(f"输出目录已存在: {output_dir}")
    
    # 遍历 PDF 目录下所有 .pdf 文件
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            process_pdf(pdf_path, output_dir)

if __name__ == "__main__":
    main()
