from flask import jsonify, request
from app.models.driver import Driver
from app import db

def get_all_drivers():
    drivers = Driver.query.all()
    return jsonify([driver.to_dict() for driver in drivers]), 200

def get_drivers_by_status(status):
    drivers = Driver.query.filter_by(status=status).all()
    return jsonify([driver.to_dict() for driver in drivers]), 200

def get_driver_by_id_or_name(identifier):
    driver = Driver.query.filter(
        (Driver.id == identifier) | (Driver.full_name.ilike(f"%{identifier}%"))
    ).first()
    if driver:
        return jsonify(driver.to_dict()), 200
    return jsonify({"message": "Driver not found"}), 404


class DriverService:
    
    @staticmethod
    def get_all_drivers():
        """Obtiene todos los conductores."""
        return Driver.query.all()

    @staticmethod
    def get_drivers_by_status(status):
        """Obtiene conductores filtrados por estado."""
        return Driver.query.filter_by(status=status).all()

    @staticmethod
    def get_driver_by_id_or_name(identifier):
        """Obtiene un conductor por ID o nombre."""
        return Driver.query.filter(
            (Driver.id == identifier) | (Driver.full_name.ilike(f"%{identifier}%"))
        ).first()