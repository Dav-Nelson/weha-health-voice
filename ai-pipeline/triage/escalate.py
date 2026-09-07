"""
Autonomous escalation for urgent triage results — the agentic "action"
component of Weha Health's maternal-health triage flow.

Sends a Telegram alert to a CHW/team contact group. This is a prototype
demonstrating the escalation pathway; it is NOT connected to real
emergency dispatch services. Fails silently (logs only) so a Telegram
outage never blocks the user from receiving their triage guidance.
"""
import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_alert(
    session_id: str,
    language: str,
    fields: dict,
    urgency: str,
    matched_signs: list,
    guidance: str
) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[escalate] Telegram not configured — skipping alert.")
        return False

    signs_text = ", ".join(s["sign"].replace("_", " ") for s in matched_signs) or "severity-based (no specific sign matched)"

    message = (
        f"🚨 WEHA HEALTH — URGENT TRIAGE ALERT (prototype)\n\n"
        f"Session: {session_id}\n"
        f"Language: {language}\n"
        f"Urgency: {urgency.upper()}\n"
        f"Danger signs: {signs_text}\n"
        f"Symptoms: {', '.join(fields.get('symptoms', []) or [])}\n"
        f"Duration: {fields.get('duration', 'unknown')}\n"
        f"Pregnant: {fields.get('is_pregnant', 'unknown')}\n"
        f"Guidance given to user: {guidance}\n\n"
        f"This is a demo/benchmark session for the Sahara CodeSwitch "
        f"Africa Challenge, not a live emergency dispatch."
    )

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[escalate] Telegram alert failed: {e}")
        return False