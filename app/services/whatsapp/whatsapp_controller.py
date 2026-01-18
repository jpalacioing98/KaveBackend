from flask import request, jsonify
from app.services.whatsapp import extract_message, send_message
from app.services.whatsapp.flows.registration_flow import registration_flow
from app.models.whatsapp_user import WhatsAppUser
from app import db
from app.models.traveler import Traveler
from app.services.whatsapp.flows.menu_flow import menu_flow, send_menu

def get_or_create_whatsapp_user(phone):
    wa_user = WhatsAppUser.query.filter_by(phone=phone).first()

    if wa_user:
        return wa_user

    traveler = Traveler.query.filter_by(phone=phone).first()

    wa_user = WhatsAppUser(
        phone=phone,
        traveler_id=traveler.id if traveler else None,
        flow="menu" if traveler else "registration",
        step=None if traveler else "start",
        temp_data={}
    )

    db.session.add(wa_user)
    db.session.commit()

    return wa_user


def handle_webhook():
    data = request.get_json()
    print("📩 WhatsApp:", data)

    sender, text = extract_message(data)
    if not sender:
        return jsonify({"status": "ignored"}), 200

    print(f"👤 Mensaje de: {sender}, Texto: '{text}'")

    wa_user = WhatsAppUser.query.filter_by(phone=sender).first()

    # 🆕 Usuario nuevo
    if not wa_user:
        print(f"🆕 Usuario nuevo detectado: {sender}")
        wa_user = WhatsAppUser(
            phone=sender,
            flow="registration",
            step="start"
        )
        db.session.add(wa_user)
        db.session.commit()
    
    print(f"📊 Estado actual - Flow: {wa_user.flow}, Step: {wa_user.step}, Traveler: {wa_user.traveler_id}")

    # ✅ ORDEN CORRECTO: Primero registro, luego menú
    
    # 🔀 Flujo de registro
    if wa_user.flow == "registration":
        print("🔄 Procesando flujo de registro")
        registration_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200
   
    # 🍔 Flujo de menú (usuario ya registrado)
    elif wa_user.flow == "menu" or wa_user.flow is None:
        print("🍔 Procesando flujo de menú")
        # Si flow es None, actualizarlo a menu
        if wa_user.flow is None:
            wa_user.flow = "menu"
            db.session.commit()
        
        menu_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200
    
    # 🚕 Flujo de viaje
    elif wa_user.flow == "trip_request":
        print("🚕 Procesando solicitud de viaje")
        send_message(wa_user.phone, "🚧 Función en desarrollo\n\nEscribe *menu* para volver al menú principal.")
        return jsonify({"status": "ok"}), 200

    # 🗓️ Flujo de viaje programado
    elif wa_user.flow == "scheduled_trip":
        print("🗓️ Procesando viaje programado")
        send_message(wa_user.phone, "🚧 Función en desarrollo\n\nEscribe *menu* para volver al menú principal.")
        return jsonify({"status": "ok"}), 200

    # 📦 Flujo de encomiendas
    elif wa_user.flow == "parcel":
        print("📦 Procesando encomiendas")
        send_message(wa_user.phone, "🚧 Función en desarrollo\n\nEscribe *menu* para volver al menú principal.")
        return jsonify({"status": "ok"}), 200

    # 🚚 Flujo de fletes
    elif wa_user.flow == "freight":
        print("🚚 Procesando fletes")
        send_message(wa_user.phone, "🚧 Función en desarrollo\n\nEscribe *menu* para volver al menú principal.")
        return jsonify({"status": "ok"}), 200
    
    # ❌ Flujo desconocido
    else:
        print(f"❌ Flujo desconocido: {wa_user.flow}")
        wa_user.flow = "menu"
        db.session.commit()
        send_menu(wa_user.phone)
        return jsonify({"status": "ok"}), 200

