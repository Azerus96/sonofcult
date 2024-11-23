import json
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import shutil
import requests
import base64
from config import Config
import logging

logger = logging.getLogger(__name__)

class GameState:
    def __init__(self):
        self.progress_dir = Config.PROGRESS_DIR
        if not os.path.exists(self.progress_dir):
            os.makedirs(self.progress_dir)

    def save_game_state(self, state: Dict):
        """Сохранение состояния игры"""
        try:
            filename = f"game_{state['game_id']}.json"
            filepath = os.path.join(self.progress_dir, filename)
            
            # Добавляем метаданные
            state['timestamp'] = datetime.now().isoformat()
            state['version'] = Config.VERSION
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
                
            # Синхронизация с GitHub
            self._sync_with_github(filename, state)
            
            # Очистка старых сохранений
            self._cleanup_old_games()
            
        except Exception as e:
            logger.error(f"Error saving game state: {str(e)}")
            raise

    def load_game_state(self, game_id: str) -> Optional[Dict]:
        """Загрузка состояния игры"""
        try:
            filename = f"game_{game_id}.json"
            filepath = os.path.join(self.progress_dir, filename)
            
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading game state: {str(e)}")
            return None

    def list_saved_games(self) -> List[Dict]:
        """Получение списка сохраненных игр"""
        try:
            if not os.path.exists(self.progress_dir):
                return []
                
            games = []
            for filename in os.listdir(self.progress_dir):
                if filename.endswith('.json') and filename.startswith('game_'):
                    filepath = os.path.join(self.progress_dir, filename)
                    with open(filepath, 'r') as f:
                        state = json.load(f)
                        games.append({
                            'game_id': state['game_id'],
                            'timestamp': state['timestamp'],
                            'current_street': state['current_street'],
                            'is_final': state.get('is_final', False)
                        })
            
            return sorted(games, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing saved games: {str(e)}")
            return []

    def _sync_with_github(self, filename: str, content: Dict):
        """Синхронизация с GitHub"""
        token = Config.AI_PROGRESS_TOKEN
        if not token:
            logger.warning("GitHub token not found, skipping sync")
            return

        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Формируем URL для API GitHub
            api_url = f"{Config.GITHUB_API_URL}/repos/{Config.GITHUB_REPO_OWNER}/{Config.GITHUB_REPO_NAME}/contents/progress/{filename}"

            # Кодируем содержимое в base64
            content_bytes = json.dumps(content, indent=2).encode('utf-8')
            content_base64 = base64.b64encode(content_bytes).decode('utf-8')

            # Проверяем существование файла
            response = requests.get(api_url, headers=headers)
            
            data = {
                'message': f'Update game progress {datetime.now().isoformat()}',
                'content': content_base64,
                'branch': 'main'
            }

            if response.status_code == 200:
                # Файл существует, добавляем его SHA
                current_file = response.json()
                data['sha'] = current_file['sha']
                
            # Отправляем запрос
            response = requests.put(api_url, headers=headers, json=data)
            
            if response.status_code not in [200, 201]:
                logger.error(f"GitHub sync failed: {response.text}")
            else:
                logger.info(f"Successfully synced {filename} with GitHub")

        except Exception as e:
            logger.error(f"Error syncing with GitHub: {str(e)}")

    def _cleanup_old_games(self):
        """Очистка старых сохранений"""
        try:
            current_time = datetime.now()
            cleanup_threshold = current_time - timedelta(days=Config.CLEANUP_DAYS)
            
            # Подсчет количества файлов
            files = []
            for filename in os.listdir(self.progress_dir):
                if filename.endswith('.json') and filename.startswith('game_'):
                    filepath = os.path.join(self.progress_dir, filename)
                    with open(filepath, 'r') as f:
                        state = json.load(f)
                        timestamp = datetime.fromisoformat(state['timestamp'])
                        files.append((filepath, timestamp))

            # Сортировка файлов по времени
            files.sort(key=lambda x: x[1], reverse=True)

            # Удаление старых файлов
            for filepath, timestamp in files[Config.MAX_SAVED_GAMES:]:
                if timestamp < cleanup_threshold:
                    os.remove(filepath)
                    logger.info(f"Removed old save file: {filepath}")

        except Exception as e:
            logger.error(f"Error cleaning up old games: {str(e)}")

    def backup_progress(self):
        """Создание резервной копии прогресса"""
        try:
            backup_dir = os.path.join(
                os.path.dirname(self.progress_dir),
                'progress_backup'
            )
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'progress_backup_{timestamp}.zip')
            
            shutil.make_archive(
                backup_file[:-4],  # remove .zip extension
                'zip',
                self.progress_dir
            )
            
            logger.info(f"Created backup: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise

    def restore_backup(self, backup_file: str):
        """Восстановление из резервной копии"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError("Backup file not found")
                
            # Очищаем текущую директорию прогресса
            if os.path.exists(self.progress_dir):
                shutil.rmtree(self.progress_dir)
                
            # Распаковываем архив
            shutil.unpack_archive(backup_file, self.progress_dir)
            
            logger.info(f"Restored from backup: {backup_file}")
            
            # Синхронизируем с GitHub после восстановления
            self._sync_all_with_github()

        except Exception as e:
            logger.error(f"Error restoring from backup: {str(e)}")
            raise

    def _sync_all_with_github(self):
        """Синхронизация всех файлов с GitHub"""
        try:
            for filename in os.listdir(self.progress_dir):
                if filename.endswith('.json') and filename.startswith('game_'):
                    filepath = os.path.join(self.progress_dir, filename)
                    with open(filepath, 'r') as f:
                        content = json.load(f)
                        self._sync_with_github(filename, content)
                        
        except Exception as e:
            logger.error(f"Error syncing all files with GitHub: {str(e)}")

    def get_game_stats(self) -> Dict:
        """Получение статистики по играм"""
        try:
            stats = {
                'total_games': 0,
                'completed_games': 0,
                'fantasy_games': 0,
                'average_score': 0,
                'highest_score': 0,
                'total_time_played': 0
            }
            
            scores = []
            for filename in os.listdir(self.progress_dir):
                if filename.endswith('.json') and filename.startswith('game_'):
                    with open(os.path.join(self.progress_dir, filename), 'r') as f:
                        state = json.load(f)
                        stats['total_games'] += 1
                        
                        if state.get('is_final'):
                            stats['completed_games'] += 1
                            if 'scores' in state:
                                player_score = state['scores']['player']['total']
                                scores.append(player_score)
                                stats['highest_score'] = max(
                                    stats['highest_score'], 
                                    player_score
                                )
                        
                        if state.get('fantasy_enabled'):
                            stats['fantasy_games'] += 1
            
            if scores:
                stats['average_score'] = sum(scores) / len(scores)
            
            return stats

        except Exception as e:
            logger.error(f"Error getting game stats: {str(e)}")
            return {}

# Глобальный экземпляр для управления состоянием
game_state = GameState()

def save_game_state(state: Dict):
    """Обертка для сохранения состояния"""
    game_state.save_game_state(state)

def load_game_state(game_id: str) -> Optional[Dict]:
    """Обертка для загрузки состояния"""
    return game_state.load_game_state(game_id)

def list_saved_games() -> List[Dict]:
    """Обертка для получения списка сохраненных игр"""
    return game_state.list_saved_games()
