from flask import Flask, jsonify
from flask_cors import CORS
import os
from src.controllers.email_controller import EmailController
from src.utils.config import Config

def create_app():
    app = Flask(__name__)
    config = Config()
    
    CORS(app, origins=["*"])
    
    email_controller = EmailController()
    
    @app.route('/api/classificar', methods=['POST'])
    def classificar_email():
        return email_controller.classificar_email()
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return email_controller.health_check()
    
    @app.route('/api')
    def api_info():
        return {
            'name': 'Email Classifier API',
            'version': '1.0.0',
            'status': 'online',
            'endpoints': {
                'classify': 'POST /api/classificar',
                'health': 'GET /api/health'
            }
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    config = Config()
    
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 8080))
    debug = False
    
    print(f"🚀 Servidor iniciando em http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)