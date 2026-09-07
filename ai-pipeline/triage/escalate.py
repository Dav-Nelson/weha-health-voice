"""
Autonomous escalation for urgent triage results — the agentic "action"
component of Weha Health's maternal-health triage flow.

Sends a WhatsApp alert (via Twilio's Sandbox) to the team's phone
numbers. This is a prototype demonstrating the escalation pathway; it
is NOT connected to real emergency dispatch services. Fails silently
(logs only) so a WhatsApp/Twilio outage never blocks the user from
receiving their own triage guidance.
"""
import os
import requests

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

TWILIO_MESSAGES_URL = (
    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    if TWILIO_ACCOUNT_SID else None
)


def _get_team_numbers() -> list:
    raw = os.environ.get("TEAM_WHATSAPP_NUMBERS", "")
    numbers = [n.strip() for n in raw.split(",") if n.strip()]
    return numbers


def send_whatsapp_alert(
    session_id: str,
    language: str,
    fields: dict,
    urgency: str,
    matched_signs: list,
    guidance: str
) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("[escalate] Twilio not configured — skipping alert.")
        return False

    team_numbers = _get_team_numbers()
    if not team_numbers:
        print("[escalate] No TEAM_WHATSAPP_NUMBERS configured — skipping alert.")
        return False

    signs_text = ", ".join(
        s["sign"].replace("_", " ") for s in matched_signs
    ) or "severity-based (no specific sign matched)"

    message_body = (
        "WEHA HEALTH - URGENT TRIAGE ALERT (prototype)\n\n"
        f"Session: {session_id}\n"
        f"Language: {language}\n"
        f"Urgency: {urgency.upper()}\n"
        f"Danger signs: {signs_text}\n"
        f"Symptoms: {', '.join(fields.get('symptoms', []) or [])}\n"
        f"Duration: {fields.get('duration', 'unknown')}\n"
        f"Pregnant: {fields.get('is_pregnant', 'unknown')}\n"
        f"Guidance given to user: {guidance}\n\n"
        "This is a demo/benchmark session for the Sahara CodeSwitch "
        "Africa Challenge, not a live emergency dispatch."
    )

    any_success = False
    for number in team_numbers:
        to_address = number if number.startswith("whatsapp:") else f"whatsapp:{number}"
        try:
            response = requests.post(
                TWILIO_MESSAGES_URL,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "From": TWILIO_WHATSAPP_FROM,
                    "To": to_address,
                    "Body": message_body
                },
                timeout=10
            )
            if response.status_code in (200, 201):
                any_success = True
            else:
                print(f"[escalate] WhatsApp send failed for {to_address}: {response.text}")
        except Exception as e:
            print(f"[escalate] WhatsApp send exception for {to_address}: {e}")

    return any_success