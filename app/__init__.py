"""
Flask application factory for the dungeon crawler game.
"""

from flask import Flask, send_from_directory
from pathlib import Path
import os


def create_app(config_name: str = 'development') -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str): Configuration name ('development', 'production', etc.)
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app with custom static folder
    frontend_dir = Path(__file__).parent / 'frontend'
    app = Flask(__name__, 
                static_folder=str(frontend_dir),
                static_url_path='/static')
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        DATA_DIR=os.environ.get('DATA_DIR', str(Path(__file__).parent.parent / 'data')),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        JSON_SORT_KEYS=False,
    )
    
    # Ensure data directory exists
    data_dir = Path(app.config['DATA_DIR'])
    data_dir.mkdir(exist_ok=True)
    
    # Register blueprints/routes
    from . import routes
    app.register_blueprint(routes.bp)
    
    # Register dev routes if DEV_MODE_KEY is set
    dev_key = os.environ.get('DEV_MODE_KEY', '')
    print(f"DEBUG: DEV_MODE_KEY from environment: '{dev_key}'")
    if dev_key:
        try:
            from . import dev_routes
            app.register_blueprint(dev_routes.dev_bp)
            print(f"✓ Developer mode enabled (access with /dev?key={dev_key})")
        except Exception as e:
            print(f"✗ Failed to register dev routes: {e}")
    else:
        print("ℹ Developer mode disabled (no DEV_MODE_KEY set)")
    
    # Register frontend routes
    _register_frontend_routes(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    return app


def _register_frontend_routes(app: Flask):
    """
    Register routes for serving the frontend.
    
    Args:
        app (Flask): Flask application instance
    """
    frontend_dir = Path(__file__).parent / 'frontend'
    sprites_dir = Path(__file__).parent / 'sprites'
    
    @app.route('/')
    def index():
        """Serve the main game interface."""
        return send_from_directory(str(frontend_dir), 'index.html')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files (CSS, JS)."""
        return send_from_directory(str(frontend_dir), filename)
    
    @app.route('/static/sprites/<path:filename>')
    def serve_sprite(filename):
        """Serve monster sprite files."""
        return send_from_directory(str(sprites_dir), filename)
    
    # Register error handlers
    _register_error_handlers(app)
    
    return app


def _register_error_handlers(app: Flask):
    """
    Register error handlers for the Flask app.
    
    Args:
        app (Flask): Flask application instance
    """
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': True,
            'message': 'Endpoint not found',
            'status_code': 404
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            'error': True,
            'message': 'Method not allowed',
            'status_code': 405
        }, 405
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'error': True,
            'message': 'Bad request - invalid JSON or missing required fields',
            'status_code': 400
        }, 400
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'error': True,
            'message': 'Internal server error',
            'status_code': 500
        }, 500