# agent.py
import os
import re
import time  # <--- Make sure time is imported at the top!
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError  # <--- Make sure APIError is imported!
import prompts
import tools

load_dotenv()

class DischargeSummaryAgent:
    def __init__(self, max_steps=5):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Error: GEMINI_API_KEY is missing from the .env file.")
        self.client = genai.Client(api_key=self.api_key)
        self.max_steps = max_steps 

    def read_patient_data(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_all_actions(self, llm_text):
        pattern = r"Action:\s*(?:CALL:\s*)?(\w+)\((.*?)\)"
        return re.findall(pattern, llm_text)

    def run_analysis_loop(self, patient_file):
        print(f"\n=== STARTING TRUE AGENT PATHWAY FOR: {os.path.basename(patient_file)} ===")
        patient_text_data = self.read_patient_data(patient_file)
        agent_scratchpad = ""
        
        system_instructions = prompts.get_system_prompt("")
        
        for step in range(1, self.max_steps + 1):
            print(f"\n--- TRUE AGENT ITERATION STEP {step}/{self.max_steps} ---")
            
            execution_prompt = (
                f"Below is the raw patient chart data:\n{patient_text_data}\n\n"
                f"Your history/scratchpad trace logs from previous runs:\n{agent_scratchpad}\n"
                f"CRITICAL: Output exactly ONE Thought and ONE Action block per step. "
                f"If you discover an extreme clinical safety concern (like a completely missing insulin regimen or a severe diagnosis conflict), "
                f"you MUST programmatically execute 'CALL: tool_escalate_to_clinician' to log it first. "
                f"You are strictly FORBIDDEN from using 'Action: FINAL_OUTPUT' until your tool history logs confirm that you have explicitly escalated these concerns. "
                f"Once all tool lookups and escalations are programmatically executed, use 'Action: FINAL_OUTPUT' and write the full summary draft directly below it."
            )

            # Hard Requirement #8: Self-healing retry engine to beat 503 traffic spikes
            response = None
            for attempt in range(1, 4):
                try:
                    response = self.client.models.generate_content(
                        model='gemini-2.5-flash',  # Keeping the high-capacity flash model
                        contents=[system_instructions, execution_prompt],
                        config={"temperature": 0.0}
                    )
                    break  # Success! Break out of the retry loop
                except APIError as e:
                    if e.code == 503 and attempt < 3:
                        print(f"Google server busy (503). Server overloading on 71-page payload. Retrying in 12 seconds... (Attempt {attempt}/3)")
                        time.sleep(12)
                    else:
                        raise e  # If it's a different error or out of retries, raise it

            step_output = response.text
            print(step_output)
            
            if "FINAL_OUTPUT" in step_output:
                print(f"\nAgent loop safely converged via explicit FINAL_OUTPUT at step {step}.")
                return step_output, agent_scratchpad

            discovered_actions = self.parse_all_actions(step_output)
            
            if discovered_actions:
                step_observations = []
                for tool_name, tool_arg in discovered_actions:
                    tool_arg_clean = tool_arg.strip("'\"")
                    print(f"Executing system tool function: {tool_name}()...")
                    
                    if tool_name == "tool_drug_interaction_lookup":
                        result = tools.tool_drug_interaction_lookup(tool_arg_clean)
                    elif tool_name == "tool_escalate_to_clinician":
                        result = tools.tool_escalate_to_clinician(tool_arg_clean)
                    else:
                        result = "Error: Unknown programmatic tool entity."
                        
                    print(f"Real Observation Appended: {result}")
                    step_observations.append(f"Observation from {tool_name}: {result}")
                
                agent_scratchpad += f"\n[Step {step} Generated]:\n{step_output}\n" + "\n".join(step_observations) + "\n"
            else:
                print(f"No active actions detected in step {step}. Appending context to prompt matrix.")
                agent_scratchpad += f"\n[Step {step} Generated]:\n{step_output}\n"

        return step_output, agent_scratchpad