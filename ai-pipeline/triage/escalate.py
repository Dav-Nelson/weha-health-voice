"""
Autonomous escalation for urgent triage results.
Sends alerts via WhatsApp (Twilio, using an approved Content Template
— WhatsApp requires this for business-initiated messages) AND
Telegram, independently, so a failure in one doesn't lose the alert.
Both fail silently (logs only).
"""
import os
import json
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_CONTENT_SID = os.environ.get("TWILIO_CONTENT_SID")

TWILIO_MESSAGES_URL = (
    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    if TWILIO_ACCOUNT_SID else None
)


def _build_alert_text(session_id, language, fields, urgency, matched_signs, guidance) -> str:
    signs_text = ", ".join(
        s["sign"].replace("_", " ") for s in matched_signs
    ) or "severity-based (no specific sign matched)"

    return (
        "URGENT TRIAGE - "
        f"Session: {session_id}. Language: {language}. "
        f"Urgency: {urgency.upper()}. Danger signs: {signs_text}. "
        f"Symptoms: {', '.join(fields.get('symptoms', []) or [])}. "
        f"Duration: {fields.get('duration', 'unknown')}. "
        f"Guidance given: {guidance}. "
        "This is a demo/benchmark session for the Sahara CodeSwitch Africa Challenge."
    )


def _get_team_whatsapp_numbers() -> list:
    raw = os.environ.get("TEAM_WHATSAPP_NUMBERS", "")
    return [n.strip() for n in raw.split(",") if n.strip()]


def send_telegram_alert(session_id, language, fields, urgency, matched_signs, guidance) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[escalate] Telegram not configured — skipping.")
        return False

    message = _build_alert_text(session_id, language, fields, urgency, matched_signs, guidance)

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


def send_whatsapp_alert(session_id, language, fields, urgency, matched_signs, guidance) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("[escalate] Twilio not configured — skipping.")
        return False

    if not TWILIO_CONTENT_SID:
        print("[escalate] TWILIO_CONTENT_SID not set — WhatsApp business-initiated "
              "messages require an approved Content Template (Twilio error 21654 "
              "otherwise). Skipping WhatsApp; Telegram still sends independently.")
        return False

    team_numbers = _get_team_whatsapp_numbers()
    if not team_numbers:
        print("[escalate] No TEAM_WHATSAPP_NUMBERS configured — skipping.")
        return False

    message_body = _build_alert_text(session_id, language, fields, urgency, matched_signs, guidance)

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
                    "ContentSid": TWILIO_CONTENT_SID,
                    "ContentVariables": json.dumps({"1": message_body[:1000]}),
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


def send_urgent_alerts(session_id, language, fields, urgency, matched_signs, guidance) -> dict:
    whatsapp_sent = send_whatsapp_alert(session_id, language, fields, urgency, matched_signs, guidance)
    telegram_sent = send_telegram_alert(session_id, language, fields, urgency, matched_signs, guidance)
    return {"whatsapp_sent": whatsapp_sent, "telegram_sent": telegram_sent}