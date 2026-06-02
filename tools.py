# tools.py
import json

def tool_drug_interaction_lookup(medication_list_str):
    meds_lower = medication_list_str.lower()
    alerts = []
    
    if not any(x in meds_lower for x in ["insulin", "actrapid", "lantus"]):
        alerts.append("CRITICAL OMISSION: Insulin therapy absent on exit prescription for a history of DKA.")
    if "oflox tz" in meds_lower and "dosage" not in meds_lower:
        alerts.append("SAFETY WARNING: 'TAB. OFLOX TZ' missing explicit dosage parameters.")
    if "zedott" in meds_lower and "lopiramide" in meds_lower:
        alerts.append("CLASS DUPLICATION: Racecadotril and Loperamide are both active.")

    return json.dumps({"status": "completed", "alerts_found": alerts})

def tool_escalate_to_clinician(reason_str):
    return json.dumps({
        "status": "ESCALATED",
        "review_channel": "SDICU_PHYSICIAN_QUEUE",
        "escalation_reason": reason_str
    })