from flask import Flask, send_from_directory
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
    
    @app.route('/')
    def serve_frontend():
        frontend_path = os.path.join(os.path.dirname(__file__), '../frontend')
        return send_from_directory(frontend_path, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        frontend_path = os.path.join(os.path.dirname(__file__), '../frontend')
        try:
            return send_from_directory(frontend_path, path)
        except:
            return {"error": "File not found"}, 404
    
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
    
    host = os.environ.get('HOST', config.HOST)
    port = int(os.environ.get('PORT', config.PORT))
    debug = os.environ.get('DEBUG', config.DEBUG) in ['True', 'true', '1']
    
    print(f"🚀 Servidor iniciando em http://{host}:{port}")
    print(f"📁 Diretório atual: {os.getcwd()}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )