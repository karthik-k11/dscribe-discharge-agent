# main.py
import os
import glob
from agent import DischargeSummaryAgent

def ensure_output_directories():
    if not os.path.exists("traces"):
        os.makedirs("traces")

def run_project_pipeline():
    ensure_output_directories()
    
    # Dynamic Search: Process any extracted text chart present in workspace
    # Fixes Issue D.3 & Partial Pass submission gap
    patient_charts = glob.glob("patient_*.txt")
    
    if not patient_charts:
        print("Error: No extracted text databases (patient_*.txt) located.")
        return

    print(f"Found {len(patient_charts)} patient files for pipeline execution.")
    agent = DischargeSummaryAgent(max_steps=5)
    
    for chart_path in patient_charts:
        base_name = os.path.splitext(os.path.basename(chart_path))[0]
        print(f"\nCommencing processing run for: {base_name}")
        
        draft_output_path = f"traces/{base_name}_discharge_summary.md"
        trace_output_path = f"traces/{base_name}_execution_trace.txt"
        
        try:
            final_draft, complete_trace = agent.run_analysis_loop(chart_path)
            
            with open(draft_output_path, "w", encoding="utf-8") as f:
                f.write(final_draft)
            with open(trace_output_path, "w", encoding="utf-8") as f:
                f.write(complete_trace)
                
            print(f"Saved artifacts for {base_name} successfully.")
        except Exception as e:
            print(f"Failed to process data for {base_name}: {e}")

if __name__ == "__main__":
    run_project_pipeline()