from app.models.user import User
from app.models.traveler import Traveler
from app import db
from app.services.whatsapp import send_message
from sqlalchemy.orm.attributes import flag_modified
from app.services.whatsapp.flows.menu_flow import send_menu
import secrets
import json

def registration_flow(wa_user, text):
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
        wa_user.step = "name"
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "👋 Bienvenido!\nPara registrarte, dime tu *nombre completo*"
        )
        return

    # ---- NOMBRE ----
    elif step == "name":
        data["full_name"] = text.strip()
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "email"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step NAME - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "📧 Ahora dime tu *correo electrónico*"
        )
        return

    # ---- EMAIL ----
    elif step == "email":
        data["email"] = text.strip().lower()
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "dni"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step EMAIL - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            "🆔 Ingresa tu *DNI*"
        )
        return

    # ---- DNI ----
    elif step == "dni":
        data["dni"] = text.strip()
        wa_user.temp_data = json.dumps(data, ensure_ascii=False)
        wa_user.step = "confirm"
        flag_modified(wa_user, 'temp_data')
        
        print("📝 Step DNI - Datos guardados:", wa_user.temp_data)
        db.session.commit()
        
        send_message(
            wa_user.phone,
            f"✅ ¿Confirmas tu registro?\n\n"
            f"*Nombre:* {data.get('full_name', 'N/A')}\n"
            f"*Email:* {data.get('email', 'N/A')}\n"
            f"*DNI:* {data.get('dni', 'N/A')}\n\n"
            f"1️⃣ Sí\n2️⃣ No"
        )
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
            
            required_fields = ["full_name", "email", "dni"]
            missing = [f for f in required_fields if f not in data or not data[f]]
            
            if missing:
                print(f"❌ Faltan campos: {missing}")
                send_message(
                    wa_user.phone,
                    f"❌ Error: Faltan datos ({', '.join(missing)}).\nEmpecemos de nuevo.\nEscribe *Hola*"
                )
                wa_user.flow = None
                wa_user.step = None
                wa_user.temp_data = None
                db.session.commit()
                return
            
            password = secrets.token_urlsafe(8)
            
            try:
                traveler = Traveler(
                    email=data["email"],
                    role="traveler",
                    full_name=data["full_name"],
                    dni=data["dni"],
                    phone=wa_user.phone
                )
                
                traveler.set_password(password)
                
                print(f"✅ Traveler creado - Email: {traveler.email}, Role: {traveler.role}")
                
                db.session.add(traveler)
                db.session.flush()
                
                print(f"✅ Traveler ID asignado: {traveler.id}")

                # ✅ Vincular y resetear ANTES del mensaje
                wa_user.traveler_id = traveler.id
                wa_user.flow = "menu"
                wa_user.step = None
                wa_user.temp_data = None
                
                db.session.commit()
                
                print(f"✅ Registro completado - Traveler ID: {traveler.id}")

                # ✅ Enviar mensaje de éxito
                send_message(
                    wa_user.phone,
                    f"🎉 *Registro exitoso!*\n\n"
                    f"📧 Email: {data['email']}\n"
                    f"🔑 Contraseña temporal: {password}\n\n"
                    f"¡Bienvenido a nuestro servicio!"
                )
                
                # ✅ Esperar un momento y mostrar menú
                import time
                time.sleep(1)  # Pequeña pausa para que los mensajes lleguen en orden
                
                from app.services.whatsapp.flows.menu_flow import send_menu
                send_menu(wa_user.phone)
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error en registro completo: {str(e)}")
                import traceback
                traceback.print_exc()
                
                send_message(
                    wa_user.phone,
                    "❌ Error al registrar. Intenta nuevamente.\nEscribe *Hola*"
                )
                wa_user.flow = None
                wa_user.step = None
                wa_user.temp_data = None
                db.session.commit()
                
        else:
            wa_user.flow = None
            wa_user.step = None
            wa_user.temp_data = None
            db.session.commit()
            
            send_message(
                wa_user.phone,
                "❌ Registro cancelado.\nEscribe *Hola* para empezar nuevamente."
            )
        
        return