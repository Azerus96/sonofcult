from flask import Blueprint, jsonify, request, render_template, current_app
from .game.table import Table
from .utils.state import save_game_state, load_game_state, list_saved_games
from .game.scoring import calculate_score
from typing import Dict
import time

bp = Blueprint('main', __name__)

# Глобальный экземпляр игрового стола
table = Table()

@bp.before_request
def before_request():
    """Действия перед каждым запросом"""
    request.start_time = time.time()

@bp.after_request
def after_request(response):
    """Действия после каждого запроса"""
    # Добавляем заголовки безопасности
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Логируем время выполнения запроса
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        current_app.logger.info(f'Request to {request.path} took {elapsed:.2f}s')
    
    return response

@bp.route('/')
def index():
    """Главная страница"""
    return render_template('game.html')

@bp.route('/api/start', methods=['POST'])
def start_game():
    """Начало новой игры"""
    try:
        result = table.start_new_game()
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f'Error starting game: {str(e)}')
        return jsonify({'error': 'Failed to start game'}), 500

@bp.route('/api/next', methods=['POST'])
def next_street():
    """Переход к следующей улице"""
    try:
        result = table.next_street()
        if result is None:
            return jsonify({'error': 'Invalid state'}), 400
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f'Error in next street: {str(e)}')
        return jsonify({'error': 'Failed to proceed to next street'}), 500

@bp.route('/api/place', methods=['POST'])
def place_card():
    """Размещение карты"""
    try:
        data = request.get_json()
        if not data or 'card' not in data or 'row' not in data or 'position' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        result = table.place_card(
            data['card'],
            data['row'],
            data['position']
        )
        return jsonify({'success': result})
    except Exception as e:
        current_app.logger.error(f'Error placing card: {str(e)}')
        return jsonify({'error': 'Failed to place card'}), 500

@bp.route('/api/load/<game_id>', methods=['GET'])
def load_game(game_id: str):
    """Загрузка сохраненной игры"""
    try:
        if table.load_game(game_id):
            return jsonify({'success': True, 'state': table.get_state()})
        return jsonify({'error': 'Game not found'}), 404
    except Exception as e:
        current_app.logger.error(f'Error loading game: {str(e)}')
        return jsonify({'error': 'Failed to load game'}), 500

@bp.route('/api/saves', methods=['GET'])
def get_saved_games():
    """Получение списка сохраненных игр"""
    try:
        return jsonify(list_saved_games())
    except Exception as e:
        current_app.logger.error(f'Error listing saved games: {str(e)}')
        return jsonify({'error': 'Failed to list saved games'}), 500

@bp.route('/api/state', methods=['GET'])
def get_game_state():
    """Получение текущего состояния игры"""
    try:
        return jsonify(table.get_state())
    except Exception as e:
        current_app.logger.error(f'Error getting game state: {str(e)}')
        return jsonify({'error': 'Failed to get game state'}), 500

@bp.route('/api/validate', methods=['POST'])
def validate_placement():
    """Проверка правильности размещения карт"""
    try:
        data = request.get_json()
        if not data or 'placement' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
            
        is_valid = table.validate_placement(data['placement'])
        return jsonify({'valid': is_valid})
    except Exception as e:
        current_app.logger.error(f'Error validating placement: {str(e)}')
        return jsonify({'error': 'Failed to validate placement'}), 500

@bp.route('/api/fantasy', methods=['POST'])
def check_fantasy():
    """Проверка возможности фантазии"""
    try:
        result = table.check_fantasy()
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f'Error checking fantasy: {str(e)}')
        return jsonify({'error': 'Failed to check fantasy'}), 500

@bp.route('/api/scores', methods=['GET'])
def get_scores():
    """Получение текущего счета"""
    try:
        scores = table.get_scores()
        return jsonify(scores)
    except Exception as e:
        current_app.logger.error(f'Error getting scores: {str(e)}')
        return jsonify({'error': 'Failed to get scores'}), 500

@bp.errorhandler(404)
def not_found_error(error):
    """Обработка ошибки 404"""
    return jsonify({'error': 'Not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    """Обработка ошибки 500"""
    current_app.logger.error(f'Server Error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': current_app.config.get('VERSION', '1.0')
    })
