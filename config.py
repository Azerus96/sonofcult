import os
from datetime import timedelta

class Config:
    # Основные настройки
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    AI_PROGRESS_TOKEN = os.environ.get('AI_PROGRESS_TOKEN')
    PROGRESS_DIR = os.path.join(os.path.dirname(__file__), 'progress')
    VERSION = '1.0.0'
    
    # Настройки сервера
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = False
    
    # Игровые константы
    CARDS_FIRST_STREET = 5
    CARDS_OTHER_STREETS = 3
    TOTAL_STREETS = 5
    
    # Размеры таблицы
    TOP_ROW_SIZE = 3
    MIDDLE_ROW_SIZE = 5
    BOTTOM_ROW_SIZE = 5

    # Таймауты
    MOVE_TIMEOUT = 30  # секунд
    GAME_TIMEOUT = 600  # секунд
    
    # Очки
    SCOOP_BONUS = 3  # Бонус за выигрыш всех линий
    
    # Очки за комбинации
    COMBINATIONS_SCORES = {
        'royal_flush': 25,
        'straight_flush': 15,
        'four_of_kind': 10,
        'full_house': 6,
        'flush': 4,
        'straight': 2,
        'three_of_kind': 2,
        'two_pairs': 1,
        'pair': 0
    }
    
    # Бонусы за специальные комбинации в верхней линии
    TOP_LINE_BONUSES = {
        'AAA': 22, 'KKK': 21, 'QQQ': 20, 'JJJ': 19,
        'TTT': 18, '999': 17, '888': 16, '777': 15,
        '666': 14, '555': 13, '444': 12, '333': 11,
        '222': 10, 'AA': 9, 'KK': 8, 'QQ': 7,
        'JJ': 6, 'TT': 5, '99': 4, '88': 3,
        '77': 2, '66': 1
    }

    # Настройки GitHub
    GITHUB_API_URL = 'https://api.github.com'
    GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPOSITORY', '').split('/')[0]
    GITHUB_REPO_NAME = os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1]

    # Настройки сохранения
    MAX_SAVED_GAMES = 100
    CLEANUP_DAYS = 30
