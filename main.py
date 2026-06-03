import os
import sys
import time
from google.genai.errors import APIError
from agent import DischargeSummaryAgent

try:
    from extract_pdf import extract_patient_pdf
except ImportError:
    def extract_patient_pdf(pdf_path):
        os.system(f"python extract_pdf.py") 

def ensure_output_directories():
    if not os.path.exists("traces"):
        os.makedirs("traces")

def run_project_pipeline():
    ensure_output_directories()
    
    # Check if the user provided a filename argument
    if len(sys.argv) < 2:
        print("Error: Missing target file argument.")
        print("Usage: python main.py <filename.pdf>")
        print("Example: python main.py patient_1.pdf")
        return

    target_pdf = sys.argv[1]
    
    if not os.path.exists(target_pdf):
        print(f"Error: The file '{target_pdf}' was not found in this directory.")
        return

    base_name = os.path.splitext(os.path.basename(target_pdf))[0]
    target_txt = f"{base_name}.txt"
    
    # Step 1: Automated extraction if the text file doesn't exist
    if not os.path.exists(target_txt):
        print(f"Extracting text from raw source: {target_pdf} -> {target_txt}...")
        extract_patient_pdf(target_pdf)
        
    if not os.path.exists(target_txt):
        print(f"Error: Extraction failed to generate '{target_txt}'.")
        return

    # Step 2: Run the Agent on the specified patient target
    print(f"\nCommencing explicit processing run for: {base_name}")
    agent = DischargeSummaryAgent(max_steps=5)
    
    draft_output_path = f"traces/{base_name}_discharge_summary.md"
    trace_output_path = f"traces/{base_name}_execution_trace.txt"
    
    for attempt in range(1, 4):
        try:
            final_draft, complete_trace = agent.run_analysis_loop(target_txt)
            
            # Save the clean draft (stripping raw agent thoughts and tokens)
            with open(draft_output_path, "w", encoding="utf-8") as f:
                if "Action: FINAL_OUTPUT" in final_draft:
                    # This removes the internal thought monologues and starts exactly at the report
                    clean_draft = final_draft.split("Action: FINAL_OUTPUT")[-1].strip()
                else:
                    clean_draft = final_draft.strip()
                f.write(clean_draft)
                
            with open(trace_output_path, "w", encoding="utf-8") as f:
                f.write(complete_trace)
                
            print(f"Saved artifacts for {base_name} successfully.")
            break 
            
        except APIError as e:
            if e.code == 503:
                print(f"Server high demand (503) on attempt {attempt}/3. Pausing 12s...")
                time.sleep(12)
            elif e.code == 429:
                print(f"Rate Limit Exhausted (429) on attempt {attempt}/3. Initiating automated 60-second cooldown cycle...")
                time.sleep(60)  # Safe buffer to let the API window reset entirely
            else:
                print(f"API Error: {e}")
                break
        except Exception as e:
            print(f"Unexpected pipeline crash: {e}")
            break

if __name__ == "__main__":
    run_project_pipeline()