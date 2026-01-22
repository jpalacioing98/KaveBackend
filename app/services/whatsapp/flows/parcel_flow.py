from urllib import response
from app import db
from app.services.whatsapp import send_message, add_hours_to_now
from sqlalchemy.orm.attributes import flag_modified
from app.controllers.parcel_controller import create_package_trip_service
import json
from datetime import datetime



def parcel_flow(wa_user, text):
    """
    Flujo para crear un envío de paquete desde WhatsApp
    (Sin manejo de ubicaciones - delegado a location_flow)
    
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
        wa_user.temp_data = "{}"
        wa_user.step = "title"
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "📦 *Nuevo Envío de Paquete*\n\n"
            "identifica tu paquete con un título breve:\n\n"
            "Ejemplo: *Documentos Importantes*"
        )
        return

     # ---- TÍTULO ----
    elif step == "title":
        data["title"] = text.strip()
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "description"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step DESCRIPTION - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "📝 añade una descripción del paquete:\n\n"
            "O escribe *skip* para omitir"
        )
        return
    # ---- DESCRIPCIÓN ----
    elif step == "description":
        data["package_description"] = text.strip()
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "weight"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step DESCRIPTION - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "⚖️ ¿Cuál es el peso del paquete en kilogramos?\n\n"
            "Ejemplo: 5.2\n"
            "O escribe *skip* para omitir"
        )
        return

    # ---- PESO ----
    elif step == "weight":
        print(f"🔍 DEBUG WEIGHT - Texto recibido: '{text}' | Tipo: {type(text)} | Longitud: {len(text)}")
        
        if text.lower().strip() != "skip":
            try:
                # Limpiar el texto: remover espacios y reemplazar coma por punto
                clean_text = text.strip().replace(',', '.')
                print(f"🔍 DEBUG WEIGHT - Texto limpio: '{clean_text}'")
                
                weight_value = float(clean_text)
                data["weight"] = weight_value
                print(f"✅ Peso guardado exitosamente: {data['weight']}")
            except ValueError as e:
                print(f"❌ Error al convertir peso: '{text}' | Error: {str(e)}")
                send_message(
                    wa_user.phone,
                    "❌ Por favor ingresa un número válido\n\n"
                    "Ejemplos válidos:\n• 5.2\n• 5,2\n• 10\n\n"
                    "O escribe *skip* para omitir"
                )
                return
            except Exception as e:
                print(f"❌ Error inesperado en weight: {str(e)}")
                import traceback
                traceback.print_exc()
                send_message(
                    wa_user.phone,
                    "❌ Ocurrió un error. Intenta de nuevo."
                )
                return
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "dimensions"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step WEIGHT - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "📏 Ingresa las dimensiones del paquete\n\n"
            "Formato: *LargoxAnchoxAlto cm*\n"
            "Ejemplo: 45x35x25 cm\n\n"
            "O escribe *skip* para omitir"
        )
        return

    # ---- DIMENSIONES ----
    elif step == "dimensions":
        if text.lower() != "skip":
            data["dimensions"] = text.strip()
        
        data["previous_flow"] = "parcel"
        data["previous_step"] = "notes"
        
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        # Cambiar flow a location para manejar ubicación de recogida
        wa_user.flow = "location"
        wa_user.step = "pickup_location"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step DIMENSIONS - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "📍 *Ubicación de Recogida*\n\n"
            "Por favor, comparte la ubicación de donde se recogerá el paquete.\n\n"
            "📎 Usa el botón de adjuntar → Ubicación"
        )
        return
    # ---- NOTAS ----
    elif step == "notes":
        if text.lower() != "skip":
            data["notes"] = text.strip()
        
        data["price"]=20000
        dt = datetime.strptime(add_hours_to_now(1), "%d/%m/%Y %H:%M")
        data["departure_time"] = dt.isoformat()
        dt = datetime.strptime(add_hours_to_now(4), "%d/%m/%Y %H:%M")
        data["arrival_time"] = dt.isoformat()
        data["previous_flow"] = "parcel"
        data["previous_step"] = "summary" 
        wa_user.flow = "driver_selection"
        wa_user.step = "start"
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        
        flag_modified(wa_user, 'temp_data')
        db.session.commit()
        
        print("📝 Step NOTES - Datos guardados:", wa_user.temp_data)
        
        
        from app.services.whatsapp.flows.driver_flow import driver_flow
        driver_flow(wa_user, "") 
        return
   
    # ---- RESUMEN ----
    elif step == "summary":
        summary = f"📦 *Resumen del Envío*\n\n"
        summary += f"*Descripción:* {data.get('package_description', 'N/A')}\n"
        if data.get('weight'):
            summary += f"*Peso:* {data['weight']} kg\n"
        if data.get('dimensions'):
            summary += f"*Dimensiones:* {data['dimensions']}\n"
        summary += f"*Precio:* ${data.get('price', 0):,.0f}\n"
        
        pickup = data.get('pickup_address', {})
        summary += f"\n📍 *Recogida:*\n{pickup.get('address_text', 'N/A')}\n"
        
        delivery = data.get('delivery_address', {})
        summary += f"\n📍 *Entrega:*\n{delivery.get('address_text', 'N/A')}\n"

        if data.get('notes'):
            summary += f"\n📝 *Notas:* {data['notes']}\n"
        
        if data.get('departure_time'):
            dt = datetime.fromisoformat(data['departure_time'])
            summary += f"\n🕐 *Recogida:* {dt.strftime('%d/%m/%Y %H:%M')}\n"
        
        if data.get('arrival_time'):
            dt = datetime.fromisoformat(data['arrival_time'])
            summary += f"🕑 *Entrega:* {dt.strftime('%d/%m/%Y %H:%M')}\n"
        
        summary += f"\n¿Confirmas el envío?\n\n1️⃣ Sí\n2️⃣ No"
        
        send_message(wa_user.phone, summary)
        wa_user.step = "confirm"
        db.session.commit()
        return
        
    # ---- CONFIRMAR ----
    elif step == "confirm":

       
        if text == "1":
            db.session.refresh(wa_user)
            
            if isinstance(wa_user.temp_data, str):
                try:
                    data = json.loads(wa_user.temp_data)
                except:
                    data = {}
            else:
                data = wa_user.temp_data or {}
            
            print("📝 Datos finales RECARGADOS:", data)
            
            # Validar campos obligatorios
            required_fields = ["package_description", "pickup_address", "delivery_address", "price"]
            missing = [f for f in required_fields if f not in data or not data[f]]
            
            if missing:
                print(f"❌ Faltan campos: {missing}")
                send_message(
                    wa_user.phone,
                    f"❌ Error: Faltan datos ({', '.join(missing)}).\n"
                    f"Empecemos de nuevo.\nEscribe *Hola*"
                )
                wa_user.flow = None
                wa_user.step = None
                wa_user.temp_data = None
                db.session.commit()
                return
            
            try:
                # Llamar a la función de creación de paquete
                response = create_package_trip_service(data)
                
                if response["success"]:
                    package_info = response["data"]
                    
                    # Resetear flujo
                    wa_user.flow = "menu"
                    wa_user.step = None
                    wa_user.temp_data = None
                    db.session.commit()
                    
                    # Mensaje de éxito
                    success_msg = f"🎉 *¡Envío Creado Exitosamente!*\n\n"
                    success_msg += f"📦 *ID:* {package_info.get('id')}\n"
                    success_msg += f"📊 *Estado:* {package_info.get('status')}\n"
                    success_msg += f"💰 *Precio:* ${data.get('price', 0):,.0f}\n\n"
                    success_msg += f"✅ Tu paquete ha sido registrado y está listo para ser asignado a un conductor."
                    
                    send_message(wa_user.phone, success_msg)
                    
                    # Volver al menú
                    from app.services.whatsapp.flows.menu_flow import send_menu
                    import time
                    time.sleep(1)
                    
                    send_menu(wa_user.phone)
                    
                else:
                    # Error en la creación
                    error_msg = response["error"]
                    send_message(
                        wa_user.phone,
                        f"❌ Error al crear el envío:\n{error_msg}\n\n"
                        f"Intenta nuevamente. Escribe *Hola*"
                    )
                    
                    wa_user.flow = None
                    wa_user.step = None
                    wa_user.temp_data = None
                    db.session.commit()
                    
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error en creación de paquete: {str(e)}")
                import traceback
                traceback.print_exc()
                
                send_message(
                    wa_user.phone,
                    "❌ Error al crear el envío. Intenta nuevamente.\nEscribe *Hola*"
                )
                wa_user.flow = None
                wa_user.step = None
                wa_user.temp_data = None
                db.session.commit()
                
        else:
            # Cancelar
            wa_user.flow = None
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "❌ Envío cancelado.\nEscribe *Hola* para volver al menú."
            )
        
        return