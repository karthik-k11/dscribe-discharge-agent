import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError # Catch cloud infrastructure errors safely

load_dotenv()

def run_multimodal_extraction(pdf_filename, output_txt_filename):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in your .env file.")
        return

    if not os.path.exists(pdf_filename):
        print(f"Error: Cannot find '{pdf_filename}' in your folder.")
        return

    print("Initializing Google GenAI Client...")
    client = genai.Client(api_key=api_key)

    print(f"Uploading '{pdf_filename}' to Google Cloud Media Storage...")
    uploaded_file = client.files.upload(file=pdf_filename)
    print(f"Upload completed. Reference: {uploaded_file.name}")

    print("Waiting briefly for cloud media layer to finalize processing...")
    while uploaded_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)
    
    if uploaded_file.state.name == "FAILED":
        print("\nGoogle Cloud failed to parse the uploaded file.")
        return
        
    print("\nCloud parsing engine ready!")

    extraction_prompt = (
        "Analyze this entire medical record PDF page-by-page. "
        "Perform a rigorous verbatim text transcription of all content. "
        "1. Transcribe all cursive and messy handwritten notes, charts, nurse observations, and checkboxes precisely.\n"
        "2. Reconstruct all numerical grids and laboratory tables into clean, readable Markdown layout tables.\n"
        "3. Output an explicit structural page marker before the content of each page, formatted exactly like this: '--- PAGE X ---' (where X is the page number).\n"
        "4. Strict Guardrail: If a word, number, or handwritten value is completely illegible or blurred, do not infer or guess it; write '[ILLEGIBLE]'."
    )

    # We will try the active available stable model tracks
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-pro']
    success = False

    for model_name in models_to_try:
        if success:
            break
            
        print(f"Attempting transcription via {model_name}...")
        # Hard Requirement #8: Try up to 3 times per model with a pause if the server flags a 503
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, extraction_prompt],
                )
                
                with open(output_txt_filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                print(f"Success! All data extracted cleanly into '{output_txt_filename}' using {model_name}!")
                success = True
                break # Exit the retry loop on success
                
            except ServerError as e:
                # Catch the 503 or 500 error specifically
                print(f"Server reported a temporary load error on attempt {attempt}/3: {e.message}")
                if attempt < 3:
                    print("Pausing for 5 seconds before retrying...")
                    time.sleep(5)
                else:
                    print(f"Completed 3 attempts on {model_name}. Moving to fallback strategy...")
            except Exception as other_err:
                print(f"Unexpected error occurred: {other_err}")
                break

    # Clean up the cloud storage reference
    print("Cleaning up remote cloud file storage...")
    client.files.delete(name=uploaded_file.name)
    
    if not success:
        print("Pipeline failed: All available cloud model paths are currently overloaded. Please run again in a moment.")

if __name__ == "__main__":
    pdf_file = "patient 2 (1).pdf"
    output_file = "patient_2.txt"
    
    run_multimodal_extraction(pdf_file, output_file)