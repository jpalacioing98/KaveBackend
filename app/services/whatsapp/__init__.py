from config import Config
from flask import Blueprint
import requests
from datetime import datetime, timedelta


whatsapp_bp = Blueprint("whatsapp", __name__)

# def extract_message(data):
#     try:
#         value = data["entry"][0]["changes"][0]["value"]
#         message = value["messages"][0]
#         sender = message["from"]
#         message_type = message["type"]

#         if message_type == "text":
#             text = message["text"]["body"].strip()
#             return sender, text.lower(), None
        
#         elif message_type == "interactive":
#             # Botón de respuesta
#             if "button_reply" in message["interactive"]:
#                 text = message["interactive"]["button_reply"]["id"]
#             # Lista de respuesta
#             elif "list_reply" in message["interactive"]:
#                 text = message["interactive"]["list_reply"]["id"]
#             else:
#                 text = None
#             return sender, text.lower() if text else None, None
        
#         elif message_type == "location":
#             location = message["location"]
#             latitude = location["latitude"]
#             longitude = location["longitude"]
            
#             # Datos opcionales
#             name = location.get("name")  # Nombre del lugar (si existe)
#             address = location.get("address")  # Dirección (si existe)
            
#             location_data = {
#                 "latitude": latitude,
#                 "longitude": longitude,
#                 "name": name,
#                 "address": address,
#                 "locations":location
#             }
            
#             return sender, None, location_data
        
#         else:
#             return sender, None, None

#     except Exception as e:
#         print(f"Error extrayendo mensaje: {e}")
#         return None, None, None
    
def extract_message(data):
    try:
        value = data["entry"][0]["changes"][0]["value"]

        # 🚫 A veces WhatsApp manda eventos sin mensajes (statuses, etc.)
        if "messages" not in value:
            return None, None, None

        message = value["messages"][0]
        sender = message.get("from")
        message_type = message.get("type")

        # =========================
        # 📩 MENSAJE DE TEXTO
        # =========================
        if message_type == "text":
            text = message["text"]["body"].strip()
            return sender, text.lower(), None

        # =========================
        # 🔘 MENSAJES INTERACTIVOS
        # (botones / listas)
        # =========================
        elif message_type == "interactive":
            interactive = message.get("interactive", {})

            if interactive.get("type") == "button_reply":
                button = interactive["button_reply"]
                return sender, button["id"].lower(), {
                    "type": "button",
                    "title": button.get("title")
                }

            elif interactive.get("type") == "list_reply":
                item = interactive["list_reply"]
                return sender, item["id"].lower(), {
                    "type": "list",
                    "title": item.get("title"),
                    "description": item.get("description")
                }

            return sender, None, None

        # =========================
        # 📍 UBICACIÓN
        # =========================
        elif message_type == "location":
            location = message["location"]

            location_data = {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "name": location.get("name"),
                "address": location.get("address"),
                "raw": location
            }

            return sender, None, location_data

        # =========================
        # ❓ OTROS TIPOS
        # =========================
        return sender, None, None

    except Exception as e:
        print(f"❌ Error extrayendo mensaje: {e}")
        return None, None, None

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

def send_confirmation_message(phone, message, yes_id="confirm_yes", no_id="confirm_no",yes_title="✅ Sí, confirmar", no_title="❌ No, cancelar"):
    """
    Envía un mensaje de confirmación con botones Sí / No vía WhatsApp

    :param phone: número destino (con código país, sin +)
    :param message: texto del mensaje de confirmación
    :param yes_id: id del botón de confirmación
    :param no_id: id del botón de cancelación
    """

    buttons = [
        {
            "id": yes_id,
            "title": yes_title
        },
        {
            "id": no_id,
            "title": no_title
        }
    ]

    return send_interactive_menu(
        phone=phone,
        body=message,
        buttons=buttons
    )


def send_continue_message(phone, message, yes_id="confirm_yes"):
    """
    Envía un mensaje de confirmación con botones Sí / No vía WhatsApp

    :param phone: número destino (con código país, sin +)
    :param message: texto del mensaje de confirmación
    :param yes_id: id del botón de confirmación
    :param no_id: id del botón de cancelación
    """

    buttons = [
        {
            "id": yes_id,
            "title": "✅ Sí, Continuar"
        },
       
    ]

    return send_interactive_menu(
        phone=phone,
        body=message,
        buttons=buttons
    )


def add_hours_to_now(hours):
    """
    Devuelve la hora del sistema sumando el número de horas indicado.
    hours: int | float (puede ser negativo)
    Retorna: datetime (hora local)
    """
    try:
        hrs = float(hours)
    except (TypeError, ValueError):
        raise ValueError("hours debe ser un número")
    return (datetime.now() + timedelta(hours=hrs)).strftime("%d/%m/%Y %H:%M")