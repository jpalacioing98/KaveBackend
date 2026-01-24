from flask import request, jsonify
from app.services.whatsapp import extract_message, send_message
from app.services.whatsapp.flows.driver_flow import driver_flow
from app.services.whatsapp.flows.registration_flow import registration_flow
from app.models.whatsapp_user import WhatsAppUser
from app import db
from app.models.traveler import Traveler
from app.services.whatsapp.flows.menu_flow import menu_flow, send_menu
from app.services.whatsapp.flows.parcel_flow import parcel_flow
from app.services.whatsapp.flows.location_flow import location_flow
from app.services.whatsapp.flows.driver_flow import driver_flow
from app.services.whatsapp.flows.one_way_flow import custom_trip_flow
from app.services.whatsapp.flows.round_flow import round_trip_flow
from app.services.whatsapp.flows.multilocation_flow import multilocation_flow


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

    sender, text, location_data = extract_message(data)
    if not sender:
        return jsonify({"status": "ignored"}), 200

    print(f"👤 Mensaje de: {sender}, Texto: '{text}', Location: {location_data is not None} ,Location_data: {location_data }")

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

    if text is None and location_data is None:
        return jsonify({"status": "ignored"}), 200
    
    # ✅ ORDEN CORRECTO: Primero registro, luego menú
    
    # 🔀 Flujo de registro
    if wa_user.flow == "registration":
        print("🔄 Procesando flujo de registro")
        registration_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200
   
    # 🍔 Flujo de menú (usuario ya registrado) 
    elif wa_user.flow == "menu" or wa_user.flow == "Menu" or wa_user.flow == "Menú" or wa_user.flow is None:
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
        custom_trip_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200

    # 🗓️ Flujo de viaje programado
    elif wa_user.flow == "round_trip":
        print("🔄 Procesando flujo de viaje Round Trip")
        round_trip_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200

    # 📦 Flujo de encomiendas
    elif wa_user.flow == "parcel":
        print("📦 Procesando flujo de paquete")
        parcel_flow(wa_user, text)
        print("📦 Estado después del flujo de paquete - Flow:", wa_user.flow, "Step:", wa_user.step)
        return jsonify({"status": "ok"}), 200
    
    # 📍 Flujo de ubicaciones (independiente)
    elif wa_user.flow == "location":
        print("📍 Procesando flujo de ubicación")
        location_flow(wa_user, text=text, location_data=location_data)
        return jsonify({"status": "ok"}), 200

    elif wa_user.flow == "multilocation":
        print("📍 Procesando flujo de ubicación")
        multilocation_flow(wa_user, text=text, location_data=location_data)
        return jsonify({"status": "ok"}), 200

    # 🚚 Flujo de fletes
    elif wa_user.flow == "freight":
        print("🚚 Procesando fletes")
        send_message(wa_user.phone, "🚧 Función en desarrollo\n\nEscribe *menu* para volver al menú principal.")
        wa_user.flow = "menu"
        db.session.commit()
        return jsonify({"status": "ok"}), 200
    
    # 🚗 Flujo de selección de conductor
    elif wa_user.flow == "driver_selection":
        print("🚗 Procesando selección de conductor")
        driver_flow(wa_user, text)
        return jsonify({"status": "ok"}), 200
    
    # ❌ Flujo desconocido
    else:
        print(f"❌ Flujo desconocido: {wa_user.flow}")
        wa_user.flow = "menu"
        db.session.commit()
        return jsonify({"status": "ok"}), 200
    



#    modo de uso del flujo de driver en otros flujos
#  elif wa_user.step == "select_driver":
#         # Guardar contexto para volver después
#         if not wa_user.temp_data:
#             wa_user.temp_data = {}
        
#         wa_user.temp_data['previous_flow'] = 'parcel'
#         wa_user.temp_data['previous_step'] = 'payment_method'  # O el step que sigue
        
#         # Cambiar a flujo de conductor
#         wa_user.flow = "driver_selection"
#         wa_user.step = "start"
#         db.session.commit()
        
#         # Iniciar el flujo
#         from app.services.whatsapp.flows.driver_flow import driver_flow
#         driver_flow(wa_user, "")
#         return