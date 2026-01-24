from app import db
from app.services.whatsapp import (
    send_message, 
    send_confirmation_message,
    send_interactive_menu,
    add_hours_to_now
)
from sqlalchemy.orm.attributes import flag_modified
from app.controllers.custom_trip_controller import CustomTripController
import json
from datetime import datetime


def round_trip_flow(wa_user, text):
    """
    Flujo para crear viajes de ida y vuelta (Round Trip) desde WhatsApp
    
    Steps:
    - start: Inicializar
    - outbound_locations: Ubicaciones de ida (delega a location_manager_flow)
    - return_locations_choice: ¿Reutilizar ubicaciones de ida?
    - return_locations: Ubicaciones de vuelta (si no reutiliza)
    - select_driver: Selección de conductor
    - confirm_driver_selection: Confirmar selección de conductor
    - notes: Notas adicionales
    - requires_wait: ¿Requiere espera?
    - wait_time: Tiempo de espera (si requiere)
    - summary: Resumen
    - confirm: Confirmación final
    
    Args:
        wa_user: Usuario de WhatsApp
        text: Texto del mensaje
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
    
    print(f"🔄 Round Trip Flow - Step: {step}, Text: '{text}'")
    
    # ---- INICIO ----
    if step == "start":
        wa_user.temp_data = json.dumps({
            "custom_trip_type": "round",
            "passenger_count": 1,
            "requires_wait": False,
            "reuse_outbound_locations": False
        }, ensure_ascii=False)
        wa_user.step = "outbound_locations"
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "🔄 *Viaje de Ida y Vuelta*\n\n"
            "Vamos a configurar las ubicaciones de tu viaje.\n\n"
            "Primero, configuremos las *ubicaciones de IDA*."
        )
        
        # Iniciar flujo de ubicaciones para IDA
        start_location_manager(wa_user, context='ida', next_step='return_locations_choice')
        return
    
    # ---- UBICACIONES DE IDA (manejado por location_manager_flow) ----
    # Este paso se activa cuando location_manager_flow termina
    
    # ---- ELEGIR UBICACIONES DE VUELTA ----
    elif step == "return_locations_choice":
        send_confirmation_message(
            wa_user.phone,
            "✅ Ubicaciones de ida configuradas.\n\n"
            "Para las ubicaciones de VUELTA:\n\n"
            "¿Deseas usar las mismas ubicaciones de ida pero en orden inverso?"
        )
        wa_user.step = "process_return_choice"
        db.session.commit()
        return
    
    # ---- PROCESAR ELECCIÓN DE VUELTA ----
    elif step == "process_return_choice":
        if text == "confirm_yes":
            # Reutilizar ubicaciones de ida (invertidas)
            data['reuse_outbound_locations'] = True
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "select_driver"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "✅ Se usarán las mismas ubicaciones en orden inverso para la vuelta."
            )
            
            # Continuar con selección de conductor
            ask_driver_selection(wa_user)
            return
        
        elif text == "confirm_no":
            # Configurar ubicaciones diferentes para vuelta
            data['reuse_outbound_locations'] = False
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "return_locations"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "Ahora configuremos las *ubicaciones de VUELTA*."
            )
            
            # Iniciar flujo de ubicaciones para VUELTA
            start_location_manager(wa_user, context='vuelta', next_step='select_driver')
            return
        
        else:
            send_message(
                wa_user.phone,
                "Por favor usa los botones para responder."
            )
            return
    
    # ---- UBICACIONES DE VUELTA (manejado por location_manager_flow) ----
    # Este paso se activa cuando location_manager_flow termina con vuelta
    
    # ---- SELECCIÓN DE CONDUCTOR ----
    elif step == "select_driver":
        ask_driver_selection(wa_user)
        return
    
    # ---- CONFIRMAR SELECCIÓN DE CONDUCTOR ----
    elif step == "confirm_driver_selection":
        from app.services.whatsapp.flows.driver_flow import driver_flow
        
        if text == "confirm_yes":
            data['previous_flow'] = "round_trip"
            data['previous_step'] = "notes"
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.flow = "driver_selection"
            wa_user.step = "start"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            driver_flow(wa_user, "")
        
        elif text == "confirm_no":
            wa_user.step = "notes"
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "📝 *Notas Adicionales*\n\n"
                "¿Tienes alguna nota o instrucción especial?\n\n"
                "O escribe *skip* para omitir"
            )
        
        return
    
    # ---- NOTAS ----
    elif step == "notes":
        if text.lower().strip() != "skip":
            data['notes'] = text.strip()
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "requires_wait"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        send_confirmation_message(
            wa_user.phone,
            "⏱️ ¿Requieres que el conductor espere en el destino antes de iniciar la vuelta?"
        )
        return
    
    # ---- ¿REQUIERE ESPERA? ----
    elif step == "requires_wait":
        if text == "confirm_yes":
            data['requires_wait'] = True
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "wait_time"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "⏱️ *Tiempo de Espera*\n\n"
                "¿Cuántos minutos necesitas que el conductor espere?\n\n"
                "Ejemplo: 30"
            )
            return
        
        elif text == "confirm_no":
            data['requires_wait'] = False
            data['wait_time_minutes'] = None
            
            # Configurar precio y tiempos
            configure_trip_pricing(data)
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "summary"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            show_trip_summary(wa_user, data)
            return
        
        else:
            send_message(
                wa_user.phone,
                "Por favor usa los botones para responder."
            )
            return
    
    # ---- TIEMPO DE ESPERA ----
    elif step == "wait_time":
        try:
            wait_minutes = int(text.strip())
            
            if wait_minutes < 0:
                send_message(
                    wa_user.phone,
                    "❌ El tiempo de espera no puede ser negativo.\n\n"
                    "Por favor ingresa un número válido de minutos."
                )
                return
            
            data['wait_time_minutes'] = wait_minutes
            
            # Configurar precio y tiempos
            configure_trip_pricing(data)
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.step = "summary"
            flag_modified(wa_user, 'temp_data')
            db.session.commit()
            
            show_trip_summary(wa_user, data)
            return
            
        except ValueError:
            send_message(
                wa_user.phone,
                "❌ Por favor ingresa un número válido de minutos.\n\n"
                "Ejemplo: 30"
            )
            return
    
    # ---- RESUMEN ----
    elif step == "summary":
        show_trip_summary(wa_user, data)
        return
    
    # ---- CONFIRMAR ----
    elif step == "confirm":
        if text == "confirm_yes":
            create_round_trip(wa_user, data)
        
        elif text == "confirm_no":
            wa_user.flow = "menu"
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "❌ Viaje cancelado.\n\nEscribe *menu* para volver al menú."
            )
        
        return


# ============== FUNCIONES AUXILIARES ==============

def start_location_manager(wa_user, context='general', next_step='summary'):
    """Inicia el flujo de gestión de ubicaciones"""
    data = json.loads(wa_user.temp_data) if isinstance(wa_user.temp_data, str) else wa_user.temp_data or {}
    
    data['location_context'] = context
    data['previous_flow'] = 'round_trip'
    data['previous_step'] = next_step
    
    wa_user.temp_data = json.dumps(data, ensure_ascii=False)
    wa_user.flow = "multilocation"
    wa_user.step = "start"
    flag_modified(wa_user, 'temp_data')
    db.session.commit()
    
    from app.services.whatsapp.flows.multilocation_flow import multilocation_flow
    multilocation_flow(wa_user, "")


def ask_driver_selection(wa_user):
    """Pregunta si desea seleccionar conductor"""
    send_confirmation_message(
        wa_user.phone,
        "¿Deseas seleccionar un conductor para el viaje ahora o dejar que los conductores acepten tu solicitud?"
    )
    wa_user.step = "confirm_driver_selection"
    db.session.commit()


def configure_trip_pricing(data):
    """Configura precio y tiempos del viaje"""
    # Precio base para Round Trip (mayor que One Way)
    base_price = 40000
    
    # Agregar costo por tiempo de espera
    if data.get('requires_wait') and data.get('wait_time_minutes'):
        wait_cost = data['wait_time_minutes'] * 200  # $200 por minuto
        data['price'] = base_price + wait_cost
    else:
        data['price'] = base_price
    
    # Configurar tiempos
    dt_departure = datetime.strptime(add_hours_to_now(1), "%d/%m/%Y %H:%M")
    data['departure_time'] = dt_departure.isoformat()
    
    # Tiempo de ida + espera + vuelta
    total_hours = 2  # Base
    if data.get('wait_time_minutes'):
        total_hours += data['wait_time_minutes'] / 60
    
    dt_arrival = datetime.strptime(add_hours_to_now(total_hours), "%d/%m/%Y %H:%M")
    data['arrival_time'] = dt_arrival.isoformat()


def show_trip_summary(wa_user, data):
    """Muestra el resumen del viaje Round Trip"""
    summary = "🔄 *Resumen del Viaje de Ida y Vuelta*\n\n"
    summary += f"*Pasajeros:* {data.get('passenger_count', 1)}\n"
    summary += f"*Precio:* ${data.get('price', 0):,.0f}\n"
    
    # Ubicaciones de ida
    locations_ida = data.get('locations_ida', [])
    summary += f"\n📍 *Ubicaciones de IDA ({len(locations_ida)}):*\n"
    for i, loc in enumerate(locations_ida, 1):
        type_icon = {"pickup": "📍", "delivery": "🎯", "waypoint": "⏸️"}.get(loc['type'], '📍')
        summary += f"{i}. {type_icon} {loc['address_text']}\n"
    
    # Ubicaciones de vuelta
    if data.get('reuse_outbound_locations'):
        summary += f"\n📍 *Ubicaciones de VUELTA:*\n"
        summary += f"↩️ Mismas ubicaciones en orden inverso\n"
    else:
        locations_vuelta = data.get('locations_vuelta', [])
        summary += f"\n📍 *Ubicaciones de VUELTA ({len(locations_vuelta)}):*\n"
        for i, loc in enumerate(locations_vuelta, 1):
            type_icon = {"pickup": "📍", "delivery": "🎯", "waypoint": "⏸️"}.get(loc['type'], '📍')
            summary += f"{i}. {type_icon} {loc['address_text']}\n"
    
    # Espera
    if data.get('requires_wait'):
        summary += f"\n⏱️ *Tiempo de espera:* {data.get('wait_time_minutes', 0)} minutos\n"
    else:
        summary += f"\n⏱️ *Sin tiempo de espera*\n"
    
    # Conductor
    if data.get('selected_driver_name'):
        summary += f"\n👤 *Conductor:* {data['selected_driver_name']}\n"
    
    # Notas
    if data.get('notes'):
        summary += f"\n📝 *Notas:* {data['notes']}\n"
    
    # Tiempos
    if data.get('departure_time'):
        dt = datetime.fromisoformat(data['departure_time'])
        summary += f"\n🕐 *Salida:* {dt.strftime('%d/%m/%Y %H:%M')}\n"
    
    if data.get('arrival_time'):
        dt = datetime.fromisoformat(data['arrival_time'])
        summary += f"🕑 *Regreso estimado:* {dt.strftime('%d/%m/%Y %H:%M')}\n"
    
    summary += f"\n¿Confirmas el viaje?\n\n"
    
    send_confirmation_message(wa_user.phone, summary)
    wa_user.step = "confirm"
    db.session.commit()


def create_round_trip(wa_user, data):
    """Crea el viaje Round Trip en la base de datos"""
    try:
        # Preparar datos para el controlador
        trip_data = prepare_round_trip_data(data)
        
        # Llamar al servicio de creación
        response = CustomTripController.create_custom_trip_service(trip_data)
        
        if response["success"]:
            trip_info = response["data"]
            
            # Resetear flujo
            wa_user.flow = "menu"
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
            # Mensaje de éxito
            success_msg = "🎉 *¡Viaje de Ida y Vuelta Creado!*\n\n"
            success_msg += f"📊 *ID:* {trip_info.get('id')}\n"
            success_msg += f"📊 *Estado:* {trip_info.get('status')}\n"
            success_msg += f"💰 *Precio:* ${data.get('price', 0):,.0f}\n\n"
            success_msg += "✅ Tu viaje ha sido registrado."
            
            send_message(wa_user.phone, success_msg)
            
            # Volver al menú
            from app.services.whatsapp.flows.menu_flow import send_menu
            import time
            time.sleep(1)
            send_menu(wa_user.phone)
            
        else:
            error_msg = response.get("error", "Error desconocido")
            send_message(
                wa_user.phone,
                f"❌ Error al crear el viaje:\n{error_msg}\n\n"
                f"Intenta nuevamente. Escribe *menu*"
            )
            
            wa_user.flow = "menu"
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en creación de Round Trip: {str(e)}")
        import traceback
        traceback.print_exc()
        
        send_message(
            wa_user.phone,
            "❌ Error al crear el viaje. Intenta nuevamente.\nEscribe *menu*"
        )
        wa_user.flow = "menu"
        wa_user.step = None
        wa_user.temp_data = None
        db.session.commit()


def prepare_round_trip_data(data):
    """Prepara los datos en el formato esperado por el controlador"""
    addresses = []
    
    # Ubicaciones de ida (order 1-99)
    locations_ida = data.get('locations_ida', [])
    for i, loc in enumerate(locations_ida, 1):
        addresses.append({
            "address_text": loc.get("address_text"),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "type": loc.get("type", "waypoint"),
            "order": i
        })
    
    # Ubicaciones de vuelta (order 100+)
    if data.get('reuse_outbound_locations'):
        # Invertir orden de ubicaciones de ida
        for i, loc in enumerate(reversed(locations_ida), 1):
            addresses.append({
                "address_text": loc.get("address_text"),
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "type": loc.get("type", "waypoint"),
                "order": 100 + i
            })
    else:
        # Usar ubicaciones de vuelta específicas
        locations_vuelta = data.get('locations_vuelta', [])
        for i, loc in enumerate(locations_vuelta, 1):
            addresses.append({
                "address_text": loc.get("address_text"),
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "type": loc.get("type", "waypoint"),
                "order": 100 + i
            })
    
    # Estructura final
    trip_data = {
        "custom_trip_type": "round",
        "passenger_count": data.get("passenger_count", 1),
        "price": data.get("price"),
        "notes": data.get("notes"),
        "departure_time": data.get("departure_time"),
        "arrival_time": data.get("arrival_time"),
        "addresses": addresses,
        # Campos específicos de Round Trip
        "requires_wait": data.get("requires_wait", False),
        "wait_time_minutes": data.get("wait_time_minutes"),
        "reuse_outbound_locations": data.get("reuse_outbound_locations", False)
    }
    
    # Agregar conductor si fue seleccionado
    if data.get("selected_driver_id"):
        trip_data["driver_id"] = data["selected_driver_id"]
    
    if data.get("selected_driver_vehicle_id"):
        trip_data["vehicle_id"] = data["selected_driver_vehicle_id"]
    
    return trip_data