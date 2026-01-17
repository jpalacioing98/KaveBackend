from flask import Blueprint
from app.controllers.custom_trip_controller import CustomTripController
from app.middleware.auth_middleware import token_required

custom_trip_bp = Blueprint("custom_trips", __name__, url_prefix="/api/custom-trips")


# Crear un nuevo viaje personalizado
@token_required
@custom_trip_bp.route("", methods=["POST"])
def create_custom_trip():
    """
    POST /api/custom-trips
    Crear un nuevo viaje personalizado (OneWay, Round, o Tour)
    """
    return CustomTripController.create_custom_trip()


# Obtener todos los viajes personalizados
@token_required
@custom_trip_bp.route("", methods=["GET"])
def get_all_custom_trips():
    """
    GET /api/custom-trips
    Obtener todos los viajes con filtros opcionales:
    - ?custom_trip_type=one_way|round|tour
    - ?status=pending|confirmed|in_progress|completed|cancelled
    - ?driver_id=123
    """
    return CustomTripController.get_all_custom_trips()


# Obtener un viaje específico
@token_required
@custom_trip_bp.route("/<int:trip_id>", methods=["GET"])
def get_custom_trip(trip_id):
    """
    GET /api/custom-trips/{trip_id}
    Obtener detalles de un viaje específico
    """
    return CustomTripController.get_custom_trip(trip_id)


# Actualizar un viaje
@token_required
@custom_trip_bp.route("/<int:trip_id>", methods=["PUT", "PATCH"])
def update_custom_trip(trip_id):
    """
    PUT/PATCH /api/custom-trips/{trip_id}
    Actualizar un viaje personalizado
    """
    return CustomTripController.update_custom_trip(trip_id)


# Cancelar un viaje
@token_required
@custom_trip_bp.route("/<int:trip_id>", methods=["DELETE"])
def delete_custom_trip(trip_id):
    """
    DELETE /api/custom-trips/{trip_id}
    Cancelar un viaje (marca como CANCELLED)
    """
    return CustomTripController.delete_custom_trip(trip_id)


# Calcular precio de tour
@token_required
@custom_trip_bp.route("/<int:trip_id>/calculate-price", methods=["GET"])
def calculate_tour_price(trip_id):
    """
    GET /api/custom-trips/{trip_id}/calculate-price
    Calcular precio total de un tour
    """
    return CustomTripController.calculate_tour_price(trip_id)


# Rutas específicas por tipo (opcionales)
@token_required
@custom_trip_bp.route("/one-way", methods=["GET"])
def get_one_way_trips():
    """GET /api/custom-trips/one-way - Obtener solo viajes OneWay"""
    from flask import request
    request.args = request.args.copy()
    request.args = {**request.args, "custom_trip_type": "one_way"}
    return CustomTripController.get_all_custom_trips()

@token_required
@custom_trip_bp.route("/round", methods=["GET"])
def get_round_trips():
    """GET /api/custom-trips/round - Obtener solo viajes Round"""
    from flask import request
    request.args = request.args.copy()
    request.args = {**request.args, "custom_trip_type": "round"}
    return CustomTripController.get_all_custom_trips()

@token_required
@custom_trip_bp.route("/tour", methods=["GET"])
def get_tour_trips():
    """GET /api/custom-trips/tour - Obtener solo viajes Tour"""
    from flask import request
    request.args = request.args.copy()
    request.args = {**request.args, "custom_trip_type": "tour"}
    return CustomTripController.get_all_custom_trips()

# Obtener viajes de un conductor específico
@token_required
@custom_trip_bp.route("/driver/<int:driver_id>", methods=["GET"])
def get_driver_trips(driver_id):
    """
    GET /api/custom-trips/driver/{driver_id}
    Obtener todos los viajes asignados a un conductor
    Parámetros opcionales:
    - ?custom_trip_type=one_way|round|tour
    - ?status=pending|confirmed|in_progress|completed|cancelled
    """
    return CustomTripController.get_driver_trips(driver_id)


# Conductor cancela/libera un viaje
@token_required
@custom_trip_bp.route("/<int:trip_id>/driver-cancel", methods=["PUT",])
def driver_cancel_trip(trip_id):
    """
    POST/PATCH /api/custom-trips/{trip_id}/driver-cancel
    Permitir que un conductor libere un viaje asignado
    El viaje vuelve a estar disponible para otros conductores
    """
    return CustomTripController.driver_cancel_trip(trip_id)



# Accept or reject a parcel
@token_required
@custom_trip_bp.route("/driver/<int:id>/request", methods=["POST"])
def parcel_request(id):
    return CustomTripController.handle_trip_request(id)






