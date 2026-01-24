from app import db
from app.services.whatsapp import (
    send_message, 
    send_confirmation_message,
    send_interactive_menu
)
from sqlalchemy.orm.attributes import flag_modified
import json


def multilocation_flow(wa_user, text, location_data=None):
    """
    Flujo REUTILIZABLE para gestionar múltiples ubicaciones
    
    Este flujo permite:
    - Seleccionar tipo de ubicación (recogida/entrega/parada)
    - Ingresar ubicación (GPS)
    - Solicitar dirección en texto si GPS no tiene dirección
    - Confirmar ubicación
    - Agregar múltiples ubicaciones
    - Retornar al flujo que lo invocó
    
    Steps:
    - start: Inicializar lista de ubicaciones
    - select_type: Seleccionar tipo de ubicación
    - input_location: Capturar GPS
    - input_address_text: Capturar dirección en texto (si GPS no tiene dirección)
    - confirm_location: Confirmar ubicación ingresada
    - ask_add_more: ¿Agregar otra ubicación?
    - save_locations: Guardar y retornar al flujo padre
    
    Args:
        wa_user: Usuario de WhatsApp
        text: Texto del mensaje
        location_data: Datos de ubicación GPS (si aplica)
    """
    step = wa_user.step
    
    # Deserializar temp_data
    if isinstance(wa_user.temp_data, str):
        try:
            data = json.loads(wa_user.temp_data)
        except:
            data = {}
    elif wa_user.temp_data is None:
        data = {}
    else:
        data = wa_user.temp_data.copy() if isinstance(wa_user.temp_data, dict) else {}
    
    print(f"📍 Multilocation Flow - Step: {step}, Text: '{text}', Has GPS: {location_data is not None}")
    
    # ---- INICIO ----
    if step == "start":
        # Inicializar estructura de ubicaciones
        location_context = data.get('location_context', 'general')  # ida, vuelta, general
        
        if f'locations_{location_context}' not in data:
            data[f'locations_{location_context}'] = []
        
        data['current_location_context'] = location_context
        data['current_location'] = {}  # Ubicación temporal en construcción
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "select_type"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        show_location_type_options(wa_user)
        return
    
    # ---- SELECCIONAR TIPO ----
    elif step == "select_type":
        location_types = {
            "1": "pickup",
            "2": "delivery", 
            "3": "waypoint"
        }
        
        location_type = location_types.get(text)
        
        if not location_type:
            send_message(
                wa_user.phone,
                "❌ Opción no válida.\n\nPor favor elige 1, 2 o 3."
            )
            return
        
        data['current_location']['type'] = location_type
        
        type_labels = {
            "pickup": "Recogida",
            "delivery": "Entrega",
            "waypoint": "Parada Intermedia"
        }
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "input_location"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        send_message(
            wa_user.phone,
            f"📍 *Ubicación de {type_labels[location_type]}*\n\n"
            f"Por favor, comparte la ubicación.\n\n"
            f"📎 Usa el botón de adjuntar → Ubicación"
        )
        return
    
    # ---- INGRESAR UBICACIÓN ----
    elif step == "input_location":
        if not location_data:
            send_message(
                wa_user.phone,
                "❌ No se recibió una ubicación válida.\n\n"
                "Por favor, comparte tu ubicación usando el botón de adjuntar."
            )
            return
        
        # Guardar datos GPS
        data['current_location']['latitude'] = location_data.get('latitude')
        data['current_location']['longitude'] = location_data.get('longitude')
        
        # ✅ VALIDACIÓN: Verificar si la dirección viene vacía o None
        address_from_gps = location_data.get('address')
        
        if not address_from_gps or address_from_gps.strip() == "":
            # GPS no tiene dirección, solicitar en texto
            print(f"⚠️ GPS sin dirección. Lat: {data['current_location']['latitude']}, Lon: {data['current_location']['longitude']}")
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "input_address_text"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "📍 *Ubicación GPS Recibida*\n\n"
                f"✅ Coordenadas guardadas correctamente.\n\n"
                f"Sin embargo, no pudimos obtener la dirección automáticamente.\n\n"
                f"Por favor, escribe la dirección o referencia de este punto:\n\n"
                f"Ejemplo: *Calle 123 #45-67, Barrio Centro*"
            )
            return
        
        # Si tiene dirección, guardarla
        data['current_location']['address_text'] = address_from_gps
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "confirm_location"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        # Mostrar confirmación
        show_location_confirmation(wa_user, data)
        return
    
    # ---- INGRESAR DIRECCIÓN EN TEXTO (Nuevo Step) ----
    elif step == "input_address_text":
        address_text = text.strip()
        
        if not address_text:
            send_message(
                wa_user.phone,
                "❌ Por favor escribe una dirección válida.\n\n"
                "Ejemplo: *Calle 123 #45-67, Barrio Centro*"
            )
            return
        
        # Guardar la dirección ingresada por el usuario
        data['current_location']['address_text'] = address_text
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "confirm_location"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        print(f"✅ Dirección manual guardada: {address_text}")
        
        # Mostrar confirmación
        show_location_confirmation(wa_user, data)
        return
    
    # ---- CONFIRMAR UBICACIÓN ----
    elif step == "confirm_location":
        if text == "confirm_yes":
            # Agregar ubicación a la lista
            context = data.get('current_location_context', 'general')
            locations_key = f'locations_{context}'
            
            if locations_key not in data:
                data[locations_key] = []
            
            # Asignar orden
            current_loc = data['current_location']
            current_loc['order'] = len(data[locations_key]) + 1
            
            data[locations_key].append(current_loc)
            
            print(f"✅ Ubicación agregada: {current_loc}")
            
            # Limpiar ubicación temporal
            data['current_location'] = {}
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "ask_add_more"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_confirmation_message(
                wa_user.phone,
                "✅ Ubicación guardada.\n\n¿Deseas agregar otra ubicación?"
            )
            return
        
        elif text == "confirm_no":
            # Volver a ingresar ubicación
            data['current_location'] = {}
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "select_type"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "🔄 Volvamos a ingresar la ubicación."
            )
            show_location_type_options(wa_user)
            return
        
        else:
            send_message(
                wa_user.phone,
                "Por favor usa los botones para confirmar."
            )
            return
    
    # ---- ¿AGREGAR MÁS? ----
    elif step == "ask_add_more":
        if text == "confirm_yes":
            # Agregar otra ubicación
            wa_user.step = "select_type"
            db.session.commit()
            show_location_type_options(wa_user)
            return
        
        elif text == "confirm_no":
            # Finalizar y guardar
            wa_user.step = "save_locations"
            db.session.commit()
            save_and_return(wa_user, data)
            return
        
        else:
            send_message(
                wa_user.phone,
                "Por favor usa los botones para responder."
            )
            return
    
    # ---- GUARDAR UBICACIONES ----
    elif step == "save_locations":
        save_and_return(wa_user, data)
        return


# ============== FUNCIONES AUXILIARES ==============

def show_location_type_options(wa_user):
    """Muestra opciones de tipo de ubicación"""
    try:
        send_interactive_menu(
            wa_user.phone,
            body="📍 *Tipo de Ubicación*\n\n¿Qué tipo de ubicación deseas agregar?",
            buttons=[
                {"id": "1", "title": "📍 Recogida"},
                {"id": "2", "title": "🎯 Destino"},
                {"id": "3", "title": "⏸️ Parada Intermedia"}
            ]
        )
    except Exception as e:
        print(f"❌ Error con botones: {e}")
        send_message(
            wa_user.phone,
            "📍 *Tipo de Ubicación*\n\n"
            "¿Qué tipo de ubicación deseas agregar?\n\n"
            "1️⃣ Recogida\n"
            "2️⃣ Destino\n"
            "3️⃣ Parada Intermedia\n\n"
            "Responde con el número."
        )


def show_location_confirmation(wa_user, data):
    """Muestra la confirmación de la ubicación capturada"""
    current_loc = data['current_location']
    type_labels = {
        "pickup": "Recogida",
        "delivery": "Destino",
        "waypoint": "Parada Intermedia"
    }
    
    message = (
        f"📍 *Ubicación Recibida*\n\n"
        f"*Tipo:* {type_labels.get(current_loc['type'], 'Ubicación')}\n"
        f"*Dirección:* {current_loc.get('address_text', 'Sin dirección')}\n"
        f"*Coordenadas:* {current_loc.get('latitude')}, {current_loc.get('longitude')}\n\n"
        f"¿Es correcta esta ubicación?"
    )
    
    send_confirmation_message(wa_user.phone, message)


def save_and_return(wa_user, data):
    """Guarda las ubicaciones y retorna al flujo padre"""
    context = data.get('current_location_context', 'general')
    locations_key = f'locations_{context}'
    locations = data.get(locations_key, [])
    
    if not locations:
        send_message(
            wa_user.phone,
            "❌ No se agregaron ubicaciones.\n\n"
            "Empecemos de nuevo. Escribe *menu*"
        )
        wa_user.flow = "menu"
        wa_user.step = None
        wa_user.temp_data = None
        db.session.commit()
        return
    
    # Resumen de ubicaciones guardadas
    summary = f"✅ *{len(locations)} Ubicación(es) Guardada(s)*\n\n"
    
    type_icons = {
        "pickup": "📍",
        "delivery": "🎯",
        "waypoint": "⏸️"
    }
    
    type_labels = {
        "pickup": "Recogida",
        "delivery": "Destino",
        "waypoint": "Parada"
    }
    
    for i, loc in enumerate(locations, 1):
        icon = type_icons.get(loc['type'], '📍')
        label = type_labels.get(loc['type'], 'Ubicación')
        summary += f"{i}. {icon} *{label}*\n   {loc.get('address_text', 'Sin dirección')}\n\n"
    
    send_message(wa_user.phone, summary)
    
    # Retornar al flujo padre
    previous_flow = data.get('previous_flow')
    previous_step = data.get('previous_step')
    
    print(f"   → Retornando a flow: {previous_flow}, step: {previous_step}")
    
    wa_user.temp_data = json.dumps(data, ensure_ascii=False)
    wa_user.flow = previous_flow
    wa_user.step = previous_step
    flag_modified(wa_user, 'temp_data')
    db.session.commit()
    
    # Continuar el flujo padre
    if previous_flow == "round_trip":
        from app.services.whatsapp.flows.round_flow import round_trip_flow
        round_trip_flow(wa_user, "")
    elif previous_flow == "custom_trip":
        from app.services.whatsapp.flows.one_way_flow import custom_trip_flow
        custom_trip_flow(wa_user, "")
    else:
        send_message(
            wa_user.phone,
            "✅ Ubicaciones guardadas.\n\nContinuando..."
        )