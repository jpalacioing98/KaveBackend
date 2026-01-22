from app import db
from app.services.whatsapp import send_message
from sqlalchemy.orm.attributes import flag_modified
import json


def location_flow(wa_user, text=None, location_data=None):
    """
    Flujo independiente para capturar ubicaciones (recogida y entrega)
    
    Args:
        wa_user: Usuario de WhatsApp
        text: Texto del mensaje (para direcciones manuales)
        location_data: Datos de ubicación compartida desde WhatsApp
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
    
    # ---- UBICACIÓN DE RECOGIDA ----
    if step == "pickup_location":
        if location_data:
            # Verificar si name y address están vacíos
            name = location_data.get("name", "")
            address = location_data.get("address", "")
            
            if not name and not address:
                # Pedir dirección manual
                data["pickup_temp"] = {
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude")
                }
                wa_user.temp_data = json.dumps(data, ensure_ascii=False)
                wa_user.step = "pickup_location_text"
                flag_modified(wa_user, 'temp_data')
                
                print("📝 Ubicación sin nombre/dirección - Solicitando texto manual")
                db.session.commit()
                
                send_message(
                    wa_user.phone,
                    "📍 He recibido la ubicación GPS.\n\n"
                    "Por favor, escribe la dirección completa de recogida:\n\n"
                    "Ejemplo: Calle 123 #45-67, Bogotá"
                )
                return
            else:
                # Guardar ubicación con datos completos
                location_text = name if name else address
                if name and address:
                    location_text = f"{name}, {address}"
                
                data["pickup_address"] = {
                    "address_text": location_text,
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude")
                }
                
                wa_user.temp_data = json.dumps(data, ensure_ascii=False)
                wa_user.flow = "location"
                wa_user.step = "delivery_location"
                flag_modified(wa_user, 'temp_data')
                
                print("📝 Step PICKUP_LOCATION - Datos guardados:", wa_user.temp_data)
                db.session.commit()
                
                send_message(
                    wa_user.phone,
                    f"✅ Ubicación de recogida guardada:\n{location_text}\n\n"
                    "📍 *Ubicación de Entrega*\n\n"
                    "Ahora comparte la ubicación donde se entregará el paquete.\n\n"
                    "📎 Usa el botón de adjuntar → Ubicación"
                )
                return
        else:
            send_message(
                wa_user.phone,
                "❌ Por favor comparte una *ubicación* usando el botón de adjuntar.\n\n"
                "📎 Adjuntar → Ubicación"
            )
            return
    
    # ---- TEXTO DE UBICACIÓN DE RECOGIDA ----
    elif step == "pickup_location_text":
        if text and text.strip():
            pickup_temp = data.get("pickup_temp", {})
            
            data["pickup_address"] = {
                "address_text": text.strip(),
                "latitude": pickup_temp.get("latitude"),
                "longitude": pickup_temp.get("longitude")
            }
            
            # Limpiar dato temporal
            if "pickup_temp" in data:
                del data["pickup_temp"]
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.flow = "location"
            wa_user.step = "delivery_location"
            flag_modified(wa_user, 'temp_data')
            
            print("📝 Step PICKUP_LOCATION_TEXT - Datos guardados:", wa_user.temp_data)
            db.session.commit()
            
            send_message(
                wa_user.phone,
                f"✅ Ubicación de recogida guardada:\n{text.strip()}\n\n"
                "📍 *Ubicación de Entrega*\n\n"
                "Ahora comparte la ubicación donde se entregará el paquete.\n\n"
                "📎 Usa el botón de adjuntar → Ubicación"
            )
        else:
            send_message(
                wa_user.phone,
                "❌ Por favor escribe la dirección de recogida.\n\n"
                "Ejemplo: Calle 123 #45-67, Bogotá"
            )
        return
    
    # ---- UBICACIÓN DE ENTREGA ----
    elif step == "delivery_location":
        
        if location_data:
            # Verificar si name y address están vacíos
            name = location_data.get("name", "")
            address = location_data.get("address", "")
            print("🚚 Location Data Received:", location_data)
            print("🚚 Name:", name, "Address:", address)
            print("🚚 wa_user.temp_data before processing:", data)



            if not name and not address:
                # Pedir dirección manual
                data["delivery_temp"] = {
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude")
                }
                wa_user.temp_data = json.dumps(data, ensure_ascii=False)
                wa_user.step = "delivery_location_text"
                flag_modified(wa_user, 'temp_data')
                
                print("📝 Ubicación sin nombre/dirección - Solicitando texto manual")
                db.session.commit()
                
                send_message(
                    wa_user.phone,
                    "📍 He recibido la ubicación GPS.\n\n"
                    "Por favor, escribe la dirección completa de entrega:\n\n"
                    "Ejemplo: Carrera 7 #32-16, Bogotá"
                )
                return
            else:
                # Guardar ubicación con datos completos
                location_text = name if name else address
                if name and address:
                    location_text = f"{name}, {address}"
                
                data["delivery_address"] = {
                    "address_text": location_text,
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude")
                }
                
                wa_user.temp_data = json.dumps(data, ensure_ascii=False)
                wa_user.flow = "parcel"
                wa_user.step = data["finaly"]
                flag_modified(wa_user, 'temp_data')
                
                print("📝 Step DELIVERY_LOCATION - Datos guardados:", wa_user.temp_data)
                db.session.commit()
                
                send_message(
                    wa_user.phone,
                    "📝 ¿Alguna nota o instrucción especial?\n\n"
                    "Ejemplo: Contiene alimentos perecederos\n\n"
                    "O escribe *skip* para omitir"
                )
        else:
            send_message(
                wa_user.phone,
                "❌ Por favor comparte una *ubicación* usando el botón de adjuntar.\n\n"
                "📎 Adjuntar → Ubicación"
            )
            return
    
    # ---- TEXTO DE UBICACIÓN DE ENTREGA ----
    elif step == "delivery_location_text":
        if text and text.strip():
            delivery_temp = data.get("delivery_temp", {})
            
            data["delivery_address"] = {
                "address_text": text.strip(),
                "latitude": delivery_temp.get("latitude"),
                "longitude": delivery_temp.get("longitude")
            }
            
            # Limpiar dato temporal
            if "delivery_temp" in data:
                del data["delivery_temp"]
            
            wa_user.temp_data = json.dumps(data, ensure_ascii=False)
            wa_user.flow = "parcel"
            wa_user.step = data["finaly"]
            flag_modified(wa_user, 'temp_data')
            
            print("📝 Step DELIVERY_LOCATION_TEXT - Datos guardados:", wa_user.temp_data)
            db.session.commit()
            
            send_message(
                wa_user.phone,
                f"✅ Ubicación de entrega guardada:\n{text.strip()}\n\n"
                "💰 ¿Cuál es el precio del envío?\n\n"
                "Ejemplo: 18000"
            )
        else:
            send_message(
                wa_user.phone,
                "❌ Por favor escribe la dirección de entrega.\n\n"
                "Ejemplo: Carrera 7 #32-16, Bogotá"
            )
        return