from app.services.whatsapp import whatsapp_bp
from app.services.whatsapp.whatsapp_controller import handle_webhook

@whatsapp_bp.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    return handle_webhook()

@whatsapp_bp.route("/webhook", methods=["GET"])
def whatsapp_verify():
    from flask import request
    from config import Config

    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == Config.VERIFY_TOKEN:
        return challenge

    return "Invalid token", 403
