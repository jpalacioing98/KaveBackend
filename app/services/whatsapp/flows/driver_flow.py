from app.services.whatsapp import send_message, send_interactive_menu
from app import db
from app.models.driver import Driver  # Asume que tienes este modelo
import json
from app.controllers.driver_controller import DriverService
from sqlalchemy.orm.attributes import flag_modified

def driver_flow(wa_user, text):
    """
    Flujo independiente para selección de conductor
    
    Steps:
    - start: Mostrar opciones (turno o elegir)
    - select_from_list: Mostrar lista de conductores disponibles
    - confirm_selection: Confirmar conductor seleccionado
    """
    text = text.strip()
    
    print(f"🚗 Driver Flow - Step: {wa_user.step}, Texto: '{text}'")
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

    
    # Paso 1: Mostrar opciones iniciales
    if wa_user.step == "start" or not wa_user.step:
        print("   → Mostrando opciones de selección")
        # send_message(
        #     wa_user.phone,
        #     "🚗 Ahora selecciona un conductor para el envío.\n\n"
        #     "Serás redirigido a la selección de conductores."
        # )
        show_driver_selection_options(wa_user)
      
    
    # Paso 2: Usuario eligió una opción
    elif wa_user.step == "choose_option":
        if text == "1":
            # Asignar conductor en turno
            print("   → Seleccionado: Conductor en turno")
            assign_driver_on_duty(wa_user)
            return
        
        elif text == "2":
            # Mostrar lista de conductores
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
    elif wa_user.step == "select_from_list":
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
    elif wa_user.step == "confirm_selection":
        if text.lower() in ["si", "sí", "s", "yes", "1"]:
            # Guardar selección y continuar con el flujo anterior
            finalize_driver_selection(wa_user)
            return
        
        elif text.lower() in ["no", "n", "2"]:
            # Volver a mostrar opciones
            print("   → Usuario rechazó, volviendo a opciones")
            wa_user.step = "start"
            db.session.commit()
            show_driver_selection_options(wa_user)
            return
        
        else:
            send_message(
                wa_user.phone,
                "❌ Por favor responde *Sí* o *No*"
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
    # Buscar el conductor en turno (el que tiene menos viajes activos o próximo en cola)
    driver_on_duty = Driver.query.filter_by(
        is_available=True,
        is_active=True,
        on_duty=True
    ).first()
    
    if not driver_on_duty:
        # Si no hay conductor específico en turno, tomar el primero disponible
        driver_on_duty = Driver.query.filter_by(
            is_available=True,
            is_active=True
        ).first()
    
    if driver_on_duty:
        # Guardar en temp_data
        if not wa_user.temp_data:
            wa_user.temp_data = {}
        
        wa_user.temp_data['selected_driver_id'] = driver_on_duty.id
        wa_user.temp_data['selected_driver_name'] = driver_on_duty.name
        
        send_message(
            wa_user.phone,
            f"✅ *Conductor asignado*\n\n"
            f"👤 {driver_on_duty.name}\n"
            f"🚗 {driver_on_duty.vehicle_model or 'Vehículo'}\n"
            f"📱 {driver_on_duty.phone}\n\n"
            f"Continuando con tu solicitud..."
        )
        
        # Volver al flujo anterior
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
        
        vehicle = driver.vehicle.make + " " + driver.vehicle.plate if driver.vehicle else "Vehículo no asignado"
        
        message += f"{i}. *{driver.full_name}*\n"
        message += f"   🚗 {vehicle}\n"
        message += "\n"
    
    message += "Responde con el *número* del conductor que deseas seleccionar."
    
    send_message(wa_user.phone, message)
    
    wa_user.step = "select_from_list"
    db.session.commit()


def confirm_driver_selection(wa_user, driver):
    """Confirma la selección del conductor"""
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


    data["selected_driver_id"] = driver.id
    data["selected_driver_name"] = driver.full_name
    data["selected_driver_vehicle_id"] = driver.vehicle.id
    data["selected_driver_phone"] = driver.phone

    message = (
        f"✅ *Has seleccionado:*\n\n"
        f"👤 {driver.full_name}\n"
        f"🚗 {driver.vehicle.make + ' ' + driver.vehicle.plate if driver.vehicle else 'Vehículo no asignado'}\n"
        f"📱 {driver.phone}\n"
    )
    
    
    message += "\n¿Confirmas esta selección?\n\nResponde *Sí* o *No*"
    
    send_message(wa_user.phone, message)
    
    wa_user.step = "confirm_selection"
    wa_user.temp_data = json.dumps(data, ensure_ascii=False)
    flag_modified(wa_user, 'temp_data')
    db.session.commit()


def finalize_driver_selection(wa_user):
    """Finaliza la selección y vuelve al flujo anterior"""
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

    driver_name = data["selected_driver_name"]
    
    send_message(
        wa_user.phone,
        f"✅ *Conductor confirmado*\n\n"
        f"👤 {driver_name}\n\n"
        f"Continuando con tu solicitud..."
    )
    
   

def return_to_previous_flow(wa_user):
    """Regresa al flujo que invocó la selección de conductor"""
    if isinstance(wa_user.temp_data, str):
        try:
            data = json.loads(wa_user.temp_data)
        except:
            data = {}
    elif wa_user.temp_data is None:
        data = {}
    else:
        data = wa_user.temp_data.copy() if isinstance(wa_user.temp_data, dict) else {}
    previous_flow = data.get('previous_flow', 'menu')
    previous_step = data.get('previous_step', '')

    print(f"   → Regresando a flow: {previous_flow}, step: {previous_step}")
    
    wa_user.flow = previous_flow
    wa_user.step = previous_step
    db.session.commit()
    
   