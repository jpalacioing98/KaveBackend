from app.services.whatsapp import send_message
from app import db

def menu_flow(wa_user, text):
    text = text.strip()

    print(f"🍔 Menu Flow - Usuario: {wa_user.phone}, Texto: '{text}'")

    # Mostrar menú principal
    if not text or text.lower() in ["menu", "hola", "menú", "hi", "hello"]:
        print("📋 Mostrando menú principal")
        send_menu(wa_user.phone)
        return

    # Opción 1: Solicitar viaje
    if text == "1":
        print("🚕 Opción 1: Solicitud de viaje")
        wa_user.flow = "trip_request"
        wa_user.step = "start"
        db.session.commit()
        
        send_message(wa_user.phone, "🚕 *Solicitud de viaje*\n\nCuéntame desde dónde viajas.")
        return

    # Opción 2: Programar viaje
    elif text == "2":
        print("🗓️ Opción 2: Programar viaje")
        wa_user.flow = "scheduled_trip"
        wa_user.step = "start"
        db.session.commit()
        send_message(wa_user.phone, "🗓️ *Programar viaje*\n\n¿Para qué fecha deseas el viaje?")
        return

    # Opción 3: Encomiendas
    elif text == "3":
        print("📦 Opción 3: Encomiendas")
        wa_user.flow = "parcel"
        wa_user.step = "start"
        db.session.commit()
        send_message(wa_user.phone, "📦 *Encomiendas*\n\n¿Qué deseas enviar?")
        return

    # Opción 4: Fletes
    elif text == "4":
        print("🚚 Opción 4: Fletes")
        wa_user.flow = "freight"
        wa_user.step = "start"
        db.session.commit()
        send_message(wa_user.phone, "🚚 *Fletes*\n\nDescribe el tipo de carga.")
        return

    # "Más opciones" - mostrar segundo menú
    elif text.lower() == "more" or text == "más":
        print("➕ Mostrando más opciones")
        send_more_menu(wa_user.phone)
        return

    # "Volver" - regresar al menú principal
    elif text.lower() == "back" or text == "volver":
        print("⬅️ Volviendo al menú principal")
        send_menu(wa_user.phone)
        return

    # Opción no válida
    else:
        print(f"❌ Opción no válida: '{text}'")
        send_message(
            wa_user.phone,
            "❌ Opción no válida.\n\nEscribe *menu* para ver las opciones disponibles."
        )
        return


def send_menu(phone):
    """
    Envía el menú principal con 3 botones (límite de WhatsApp)
    """
    from app.services.whatsapp import send_interactive_menu
    
    print(f"📤 Enviando menú principal a {phone}")
    
    try:
        send_interactive_menu(
            phone,
            body="📋 *Menú Principal*\n\n¿Qué servicio necesitas?",
            buttons=[
                {"id": "1", "title": "🚕 Solicitar viaje"},
                {"id": "2", "title": "🗓️ Programar viaje"},
                {"id": "more", "title": "➕ Más opciones"}
            ]
        )
        print("✅ Menú principal enviado")
        
    except Exception as e:
        print(f"❌ Error al enviar menú: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback a mensaje de texto
        send_message(
            phone,
            "📋 *Menú Principal*\n\n"
            "1️⃣ Solicitar viaje\n"
            "2️⃣ Programar viaje\n"
            "➕ Escribe *más* para ver más opciones\n\n"
            "Responde con el número de tu opción."
        )


def send_more_menu(phone):
    """
    Envía el menú de opciones adicionales
    """
    from app.services.whatsapp import send_interactive_menu
    
    print(f"📤 Enviando menú de más opciones a {phone}")
    
    try:
        send_interactive_menu(
            phone,
            body="📋 *Más Opciones*\n\n¿Qué necesitas?",
            buttons=[
                {"id": "3", "title": "📦 Encomiendas"},
                {"id": "4", "title": "🚚 Fletes"},
                {"id": "back", "title": "⬅️ Volver"}
            ]
        )
        print("✅ Menú de más opciones enviado")
        
    except Exception as e:
        print(f"❌ Error al enviar menú: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback a mensaje de texto
        send_message(
            phone,
            "📋 *Más Opciones*\n\n"
            "3️⃣ Encomiendas\n"
            "4️⃣ Fletes\n"
            "⬅️ Escribe *volver* para el menú principal\n\n"
            "Responde con el número de tu opción."
        )