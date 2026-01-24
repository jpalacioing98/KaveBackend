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


def custom_trip_flow(wa_user, text):
    """
    Flujo para crear viajes personalizados One Way desde WhatsApp
    
    Steps:
    - start: Mostrar opciones de tipo de viaje
    - trip_style: Procesar tipo (reservado/compartido)
    - pickup_location: Delegar a location_flow
    - delivery_location: Delegar a location_flow
    - select_driver: Delegar a driver_flow
    - notes: Solicitar notas adicionales
    - summary: Mostrar resumen
    - confirm: Confirmar y crear
    
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

    # ---- INICIO ----
    if step == "start":
        wa_user.temp_data = json.dumps({
            "custom_trip_type": "one_way",
            "passenger_count": 1
        }, ensure_ascii=False)
        wa_user.step = "trip_style"
        db.session.commit()
        
        show_trip_style_options(wa_user)
        return

    # ---- ESTILO DE VIAJE ----
    elif step == "trip_style":
        if text == "1":
            # Viaje inmediato privado
            data["is_reserved"] = False
            data["allow_shared_ride"] = False
            trip_type_msg = "Viaje Inmediato - Privado"
        elif text == "2":
            # Viaje inmediato compartido
            data["is_reserved"] = False
            data["allow_shared_ride"] = True
            trip_type_msg = "Viaje Inmediato - Compartido"
        elif text == "3":
            # Viaje reservado privado
            data["is_reserved"] = True
            data["allow_shared_ride"] = False
            trip_type_msg = "Viaje Reservado - Privado"
        elif text == "4":
            # Viaje reservado compartido
            data["is_reserved"] = True
            data["allow_shared_ride"] = True
            trip_type_msg = "Viaje Reservado - Compartido"
        else:
            send_message(
                wa_user.phone,
                "❌ Opción no válida.\n\nPor favor elige un número del 1 al 4."
            )
            return
        
        # Guardar y continuar
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        flag_modified(wa_user, 'temp_data')
        
        # Configurar para location_flow
        data["previous_flow"] = "trip_request"
        data["previous_step"] = "confirm_driver_selection"
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.flow = "location"
        wa_user.step = "pickup_location"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        send_message(
            wa_user.phone,
            f"✅ Has seleccionado: *{trip_type_msg}*\n\n"
            f"📍 *Ubicación de Recogida*\n\n"
            f"Por favor, comparte la ubicación de donde te recogeremos.\n\n"
            f"📎 Usa el botón de adjuntar → Ubicación"
        )
        return

    # ---- SELECCIÓN DE CONDUCTOR ----
    elif step == "select_driver":
        data["previous_flow"] = "trip_request"
        data["previous_step"] = "notes"
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        send_confirmation_message(
            wa_user.phone,
            message="¿Deseas seleccionar un conductor para el viaje ahora o dejar que los conductores acepten tu solicitud?\n\n"
        )
        
        wa_user.step = "confirm_driver_selection"
        db.session.commit()
        return

    # ---- CONFIRMAR SELECCIÓN DE CONDUCTOR ----
    elif step == "confirm_driver_selection":
        from app.services.whatsapp.flows.driver_flow import driver_flow
        
        if text == "confirm_yes":
            wa_user.flow = "driver_selection"
            wa_user.step = "start"
            data["previous_flow"] = "trip_request"
            data["previous_step"] = "notes"
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            db.session.commit()
            driver_flow(wa_user, "")
        elif text == "confirm_no":
            wa_user.flow = "trip_request"
            wa_user.step = "notes"
            db.session.commit()
            
       
        return

    # ---- NOTAS ----
    elif step == "notes":
        if text.lower().strip() != "skip":
            data["notes"] = text.strip()
        
        # Configurar precio y tiempos (valores por defecto)
        data["price"] = 25000  # Precio base para One Way
        
        # Si es reservado, usar hora especificada, si no, inmediato
        if data.get("is_reserved"):
            dt = datetime.strptime(add_hours_to_now(2), "%d/%m/%Y %H:%M")
        else:
            dt = datetime.strptime(add_hours_to_now(0.5), "%d/%m/%Y %H:%M")
        
        data["departure_time"] = dt.isoformat()
        
        # Tiempo de llegada estimado (1 hora después)
        dt_arrival = datetime.strptime(add_hours_to_now(1.5 if data.get("is_reserved") else 1), "%d/%m/%Y %H:%M")
        data["arrival_time"] = dt_arrival.isoformat()
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "summary"
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        print("📝 Step NOTES - Datos guardados:", wa_user.temp_data)
        
        # Mostrar resumen automáticamente
        show_trip_summary(wa_user, data)
        return

    # ---- RESUMEN ----
    elif step == "summary":
        show_trip_summary(wa_user, data)
        return

    # ---- CONFIRMAR ----
    elif step == "confirm":
        if text == "confirm_yes":
            db.session.refresh(wa_user)
            
            if isinstance(wa_user.temp_data, str):
                try:
                    data = json.loads(wa_user.temp_data)
                except:
                    data = {}
            else:
                data = wa_user.temp_data or {}
            
            print("📝 Datos finales para crear viaje:", data)
            
            # Validar campos obligatorios
            required_fields = ["pickup_address", "delivery_address", "price"]
            missing = [f for f in required_fields if f not in data or not data[f]]
            
            if missing:
                print(f"❌ Faltan campos: {missing}")
                send_message(
                    wa_user.phone,
                    f"❌ Error: Faltan datos ({', '.join(missing)}).\n"
                    f"Empecemos de nuevo.\nEscribe *menu*"
                )
                wa_user.flow = "menu"
                wa_user.step = None
                wa_user.temp_data = None
                db.session.commit()
                return
            
            try:
                # Preparar datos para el controlador
                trip_data = prepare_trip_data_for_controller(data)
                
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
                    trip_style = "Reservado" if data.get("is_reserved") else "Inmediato"
                    share_style = "Compartido" if data.get("allow_shared_ride") else "Privado"
                    
                    success_msg = f"🎉 *¡Viaje Creado Exitosamente!*\n\n"
                    success_msg += f"🚗 *Tipo:* {trip_style} - {share_style}\n"
                    success_msg += f"📊 *ID:* {trip_info.get('id')}\n"
                    success_msg += f"📊 *Estado:* {trip_info.get('status')}\n"
                    success_msg += f"💰 *Precio:* ${data.get('price', 0):,.0f}\n\n"
                    success_msg += f"✅ Tu viaje ha sido registrado."
                    
                    if not data.get("selected_driver_id"):
                        success_msg += " Los conductores disponibles podrán aceptar tu solicitud."
                    
                    send_message(wa_user.phone, success_msg)
                    
                    # Volver al menú
                    from app.services.whatsapp.flows.menu_flow import send_menu
                    import time
                    time.sleep(1)
                    send_menu(wa_user.phone)
                    
                else:
                    # Error en la creación
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
                print(f"❌ Error en creación de viaje: {str(e)}")
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
                
        else:
            # Cancelar
            wa_user.flow = "menu"
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "❌ Viaje cancelado.\nEscribe *menu* para volver al menú."
            )
        
        return


# ============== FUNCIONES AUXILIARES ==============

def show_trip_style_options(wa_user):
    """Muestra las opciones de estilo de viaje"""
    try:
        send_interactive_menu(
            wa_user.phone,
            body="🚗 *Tipo de Viaje One Way*\n\n¿Qué tipo de viaje necesitas?",
            buttons=[
                {"id": "1", "title": "🚀 Inmediato - Privado"},
                {"id": "2", "title": "👥 Inmediato - Compartido"},
                {"id": "3", "title": "📅 Reservado - Privado"},
                {"id": "4", "title": "📅👥 Reservado - Compartido"}
            ]
        )
        print("✅ Opciones de viaje enviadas (botones)")
        
    except Exception as e:
        print(f"❌ Error con botones, usando texto: {e}")
        send_message(
            wa_user.phone,
            "🚗 *Tipo de Viaje One Way*\n\n"
            "¿Qué tipo de viaje necesitas?\n\n"
            "1️⃣ Inmediato - Privado (solo tú)\n"
            "2️⃣ Inmediato - Compartido (con otros pasajeros)\n"
            "3️⃣ Reservado - Privado (programado)\n"
            "4️⃣ Reservado - Compartido (programado con otros)\n\n"
            "Responde con el número de tu opción."
        )


def show_trip_summary(wa_user, data):
    """Muestra el resumen del viaje antes de confirmar"""
    trip_style = "Reservado" if data.get("is_reserved") else "Inmediato"
    share_style = "Compartido" if data.get("allow_shared_ride") else "Privado"
    
    summary = f"🚗 *Resumen del Viaje*\n\n"
    summary += f"*Tipo:* {trip_style} - {share_style}\n"
    summary += f"*Pasajeros:* {data.get('passenger_count', 1)}\n"
    summary += f"*Precio:* ${data.get('price', 0):,.0f}\n"
    
    pickup = data.get('pickup_address', {})
    summary += f"\n📍 *Recogida:*\n{pickup.get('address_text', 'N/A')}\n"
    
    delivery = data.get('delivery_address', {})
    summary += f"\n📍 *Destino:*\n{delivery.get('address_text', 'N/A')}\n"
    
    if data.get('selected_driver_name'):
        summary += f"\n👤 *Conductor:* {data['selected_driver_name']}\n"
    
    if data.get('notes'):
        summary += f"\n📝 *Notas:* {data['notes']}\n"
    
    if data.get('departure_time'):
        dt = datetime.fromisoformat(data['departure_time'])
        summary += f"\n🕐 *Salida:* {dt.strftime('%d/%m/%Y %H:%M')}\n"
    
    summary += f"\n¿Confirmas el viaje?\n\n"
    
    send_confirmation_message(wa_user.phone, summary)
    wa_user.step = "confirm"
    db.session.commit()


def prepare_trip_data_for_controller(data):
    """Prepara los datos en el formato esperado por el controlador"""
    # Crear estructuras de direcciones
    addresses = []
    
    # Dirección de recogida
    pickup = data.get("pickup_address", {})
    addresses.append({
        "address_text": pickup.get("address_text"),
        "latitude": pickup.get("latitude"),
        "longitude": pickup.get("longitude"),
        "type": "pickup",
        "order": 1
    })
    
    # Dirección de destino
    delivery = data.get("delivery_address", {})
    addresses.append({
        "address_text": delivery.get("address_text"),
        "latitude": delivery.get("latitude"),
        "longitude": delivery.get("longitude"),
        "type": "delivery",
        "order": 2
    })
    
    # Estructura final
    trip_data = {
        "custom_trip_type": "one_way",
        "passenger_count": data.get("passenger_count", 1),
        "price": data.get("price"),
        "notes": data.get("notes"),
        "departure_time": data.get("departure_time"),
        "addresses": addresses,
        # Campos específicos de One Way
        "allow_shared_ride": data.get("allow_shared_ride", False),
        "is_reserved": data.get("is_reserved", False)
    }
    
    # Agregar conductor si fue seleccionado
    if data.get("selected_driver_id"):
        trip_data["driver_id"] = data["selected_driver_id"]
    
    if data.get("selected_driver_vehicle_id"):
        trip_data["vehicle_id"] = data["selected_driver_vehicle_id"]
    
    return trip_data