from config import Config
from flask import Blueprint
import requests


whatsapp_bp = Blueprint("whatsapp", __name__)

def extract_message(data):
    try:
        value = data["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        sender = message["from"]

        if message["type"] == "text":
            text = message["text"]["body"].strip()
        elif message["type"] == "interactive":
            text = message["interactive"]["button_reply"]["id"]
        else:
            text = None

        return sender, text.lower() if text else None

    except Exception:
        return None, None


def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{Config.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {Config.ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=payload)

def send_interactive_menu(phone, body, buttons):
    """
    Envía botones interactivos (máximo 3)
    Raises ValueError si hay más de 3 botones
    Raises Exception si la API falla
    """
   

    # ✅ Validar límite de 3 botones
    if len(buttons) > 3:
        raise ValueError(f"WhatsApp solo permite máximo 3 botones interactivos. Se intentaron enviar {len(buttons)}")

    url = f"https://graph.facebook.com/v20.0/{Config.PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"][:20]  # ✅ WhatsApp limita títulos a 20 caracteres
                        }
                    }
                    for btn in buttons
                ]
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {Config.ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"📤 Enviando mensaje interactivo a {phone}")
    print(f"   Botones: {[btn['title'] for btn in buttons]}")

    response = requests.post(url, headers=headers, json=payload)
    
    # ✅ Manejar errores de la API
    if response.status_code != 200:
        error_msg = f"WhatsApp API error {response.status_code}: {response.text}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    print(f"✅ Mensaje interactivo enviado exitosamente")
    return response.json()