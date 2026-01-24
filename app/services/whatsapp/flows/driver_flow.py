from app.services.whatsapp import send_confirmation_message, send_message, send_interactive_menu, send_continue_message
from app import db
from app.models.driver import Driver
import json
from app.controllers.driver_controller import DriverService
from sqlalchemy.orm.attributes import flag_modified


def get_temp_data(wa_user):
    """Helper para deserializar temp_data de forma segura"""
    if isinstance(wa_user.temp_data, str):
        try:
            return json.loads(wa_user.temp_data)
        except:
            return {}
    elif wa_user.temp_data is None:
        return {}
    else:
        return wa_user.temp_data.copy() if isinstance(wa_user.temp_data, dict) else {}


def save_temp_data(wa_user, data):
    """Helper para guardar temp_data de forma segura"""
    wa_user.temp_data = json.dumps(data, ensure_ascii=False)
    flag_modified(wa_user, 'temp_data')
    db.session.commit()


def driver_flow(wa_user, text, ):
    """
    Flujo independiente para selección de conductor
    
    Steps:
    - start: Mostrar opciones (turno o elegir)
    - choose_option: Procesar opción seleccionada
    - select_from_list: Mostrar lista de conductores disponibles
    - confirm_selection: Confirmar conductor seleccionado
    """
    text = text.strip()
    step = wa_user.step
    
    print(f"🚗 Driver Flow - Step: {step}, Texto: '{text}'")
    
    data = get_temp_data(wa_user)
    
    # Paso 1: Mostrar opciones iniciales
    if step == "start" or not step:
        print("   → Mostrando opciones de selección")
        show_driver_selection_options(wa_user)
        return
      
    # Paso 2: Usuario eligió una opción
    elif step == "choose_option":
        if text == "1":
            print("   → Seleccionado: Conductor en turno")
            assign_driver_on_duty(wa_user)
            return
        
        elif text == "2":
            print("   → Mostrar lista de conductores")
            show_available_drivers(wa_user)
            return
        
        else:
            send_message(
                wa_user.phone,
                "❌ Opción no válida.\n\nResponde *1* o *2*"
            )
            return
    
    # Paso 3: Usuario está seleccionando de la lista
    elif step == "select_from_list":
        try:
            selection = int(text)
            available_drivers = DriverService.get_all_drivers()
            
            if 1 <= selection <= len(available_drivers):
                selected_driver = available_drivers[selection - 1]
                confirm_driver_selection(wa_user, selected_driver)
                return
            else:
                send_message(
                    wa_user.phone,
                    f"❌ Número inválido.\n\nPor favor elige un número entre 1 y {len(available_drivers)}"
                )
                return
                
        except ValueError:
            send_message(
                wa_user.phone,
                "❌ Por favor responde con el número del conductor que deseas seleccionar."
            )
            return
    
    # Paso 4: Confirmar selección
    elif step == "confirm_selection":

        if text == "confirm_yes":
            print("   → Usuario confirmó selección")
            finalize_driver_selection(wa_user)
            return

        elif text == "confirm_no":
            print("   → Usuario rechazó, volviendo a opciones")
            wa_user.step = "start"
            db.session.commit()
            show_driver_selection_options(wa_user)
            return

        else:
            send_message(
                wa_user.phone,
                "Por favor usa los botones para confirmar la selección."
            )
            return



def show_driver_selection_options(wa_user):
    """Muestra las opciones para seleccionar conductor"""
    try:
        send_interactive_menu(
            wa_user.phone,
            body="🚗 *Selección de Conductor*\n\n¿Cómo deseas asignar el conductor?",
            buttons=[
                {"id": "1", "title": "👤 Conductor en turno"},
                {"id": "2", "title": "📋 Elegir conductor"}
            ]
        )
        print("✅ Opciones de conductor enviadas (botones)")
        
    except Exception as e:
        print(f"❌ Error con botones, usando texto: {e}")
        send_message(
            wa_user.phone,
            "🚗 *Selección de Conductor*\n\n"
            "¿Cómo deseas asignar el conductor?\n\n"
            "1️⃣ Conductor en turno (automático)\n"
            "2️⃣ Elegir conductor de la lista\n\n"
            "Responde con el número de tu opción."
        )
    
    wa_user.step = "choose_option"
    db.session.commit()


def assign_driver_on_duty(wa_user):
    """Asigna automáticamente el conductor en turno"""
    driver = DriverService.get_drivers_by_status("assigned").first()
    
    if driver:
        # ✅ FIX: Obtener y guardar datos correctamente
        data = get_temp_data(wa_user)
        
        data["selected_driver_id"] = driver.id
        data["selected_driver_name"] = driver.full_name
        data["selected_driver_vehicle_id"] = driver.vehicle.id if driver.vehicle else None
        data["selected_driver_phone"] = driver.phone
        
        # ✅ FIX: Guardar en base de datos
        save_temp_data(wa_user, data)
        
        vehicle_info = f"{driver.vehicle.make} {driver.vehicle.plate}" if driver.vehicle else "Vehículo no asignado"
        
        message = (
            f"✅ *Conductor asignado automáticamente:*\n\n"
            f"👤 {driver.full_name}\n"
            f"🚗 {vehicle_info}\n"
            f"📱 {driver.phone}\n\n"
            f"Continuando con tu solicitud..."
        )
        
        send_message(wa_user.phone, message)
        
        # ✅ FIX: Regresar al flujo anterior
        return_to_previous_flow(wa_user)
        
    else:
        send_message(
            wa_user.phone,
            "❌ No hay conductores disponibles en este momento.\n\n"
            "Por favor intenta más tarde o escribe *menu* para volver."
        )
        wa_user.flow = "menu"
        wa_user.step = None
        db.session.commit()


def show_available_drivers(wa_user):
    """Muestra lista numerada de conductores disponibles"""
    available_drivers = DriverService.get_all_drivers()
    
    if not available_drivers:
        send_message(
            wa_user.phone,
            "❌ No hay conductores disponibles en este momento.\n\n"
            "Escribe *menu* para volver al menú principal."
        )
        wa_user.flow = "menu"
        wa_user.step = None
        db.session.commit()
        return
    
    # Construir mensaje con lista
    message = "🚗 *Conductores Disponibles*\n\n"
    
    for i, driver in enumerate(available_drivers, 1):
        vehicle = f"{driver.vehicle.make} {driver.vehicle.plate}" if driver.vehicle else "Vehículo no asignado"
        
        message += f"{i}. *{driver.full_name}*\n"
        message += f"   🚗 {vehicle}\n"
        message += f"   📱 {driver.phone}\n\n"
    
    message += "Responde con el *número* del conductor que deseas seleccionar."
    
    send_message(wa_user.phone, message)
    
    wa_user.step = "select_from_list"
    db.session.commit()


def confirm_driver_selection(wa_user, driver):
    """Confirma la selección del conductor"""
    data = get_temp_data(wa_user)
    
    data["selected_driver_id"] = driver.id
    data["selected_driver_name"] = driver.full_name
    data["selected_driver_vehicle_id"] = driver.vehicle.id if driver.vehicle else None
    data["selected_driver_phone"] = driver.phone
    
    vehicle_info = f"{driver.vehicle.make} {driver.vehicle.plate}" if driver.vehicle else "Vehículo no asignado"
    
    message = (
        f"👤 *Has seleccionado el siguiente conductor:*\n\n"
        f"👤 {driver.full_name}\n"
        f"🚗 {vehicle_info}\n"
        f"📱 {driver.phone}\n\n"
        f"¿Confirmas esta selección?"
    )

    # 👇 USAR TU SISTEMA REAL DE CONFIRMACIÓN
    send_confirmation_message(wa_user.phone, message)

    save_temp_data(wa_user, data)

    wa_user.step = "confirm_selection"
    db.session.commit()


def finalize_driver_selection(wa_user):
    """Finaliza la selección y vuelve al flujo anterior"""
    data = get_temp_data(wa_user)
    driver_name = data.get("selected_driver_name", "Conductor")
    
    send_message(
        wa_user.phone,
        f"✅ *Conductor confirmado*\n\n"
        f"👤 {driver_name}\n\n"
        f"Continuando con tu solicitud..."
    )
    
    # ✅ FIX: Llamar a return_to_previous_flow
    return_to_previous_flow(wa_user)


def return_to_previous_flow(wa_user):
    """Regresa al flujo que invocó la selección de conductor"""
    data = get_temp_data(wa_user)
    
    previous_flow = data.get('previous_flow')
    previous_step = data.get('previous_step')  # ✅ FIX: Cambiado a 'notes' para parcel_flow
    
    print(f"   → Regresando a flow: {previous_flow}, step: {previous_step}")
    
    wa_user.flow = previous_flow
    wa_user.step = previous_step
    db.session.commit()
    
    if previous_flow == "parcel":
        send_continue_message(
            wa_user.phone,
            "✅ Has seleccionado un conductor.\n\n"
            "Continuemos con el proceso."   
        )
    elif previous_flow == "trip_request":
        send_message(
                wa_user.phone,
                "📝 *Notas Adicionales*\n\n"
                "¿Tienes alguna nota o instrucción especial para el conductor?\n\n"
                "O escribe *skip* para omitir"
            )
    elif previous_flow == "round_trip":
        send_message(
                wa_user.phone,
                "📝 *Notas Adicionales*\n\n"
                "¿Tienes alguna nota o instrucción especial?\n\n"
                "O escribe *skip* para omitir"
            )
        