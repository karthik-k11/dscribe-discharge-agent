import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_filename, output_txt_filename):
    print(f"Starting extraction from {pdf_filename}...")
    
    # Check if the PDF file actually exists in the folder
    if not os.path.exists(pdf_filename):
        print(f"Error: Could not find '{pdf_filename}' in this folder. Please check the name.")
        return

    reader = PdfReader(pdf_filename)
    
    with open(output_txt_filename, "w", encoding="utf-8") as f:
        # Loop through every page of the PDF sequentially
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text()
            
            # Write a clear page marker so our AI agent knows exactly where it is looking
            f.write(f"\n--- PAGE {page_num} ---\n")
            if text:
                f.write(text)
            else:
                f.write("[Image or handwritten text layout encountered]\n")
                
    print(f"Success! Text completely extracted and saved to '{output_txt_filename}'")

if __name__ == "__main__":
    # Make sure this matches the exact filename of the PDF you placed in your folder
    pdf_file = "patient 2 (1).pdf" 
    output_file = "patient_2.txt"
    
    extract_text_from_pdf(pdf_file, output_file)