from typing import Dict, List, Optional
from ..game.deck import Card
from ..game.player import Player
from ..game.scoring import calculate_score
from .mccfr import MCCFR, GameState
import os
import json

class AIStrategy:
    def __init__(self):
        self.mccfr = MCCFR()
        self.load_progress()
        
    def initialize(self):
        """Инициализация стратегии"""
        initial_state = self._get_initial_state()
        self.mccfr.train(initial_state, iterations=1000)
        self.save_progress()
        
    def make_move(self, game_state: Dict) -> Optional[Dict]:
        """Выполнение хода ИИ"""
        state = self._create_game_state(game_state)
        action = self.mccfr.get_action(state)
        
        if not action:
            return None
            
        card_str, row, pos = action.split('_')
        return {
            'card': {
                'rank': card_str[0],
                'suit': card_str[1]
            },
            'row': row,
            'position': int(pos)
        }
        
    def _get_initial_state(self) -> GameState:
        """Получение начального состояния игры"""
        return GameState(
            player_cards=[],
            placed_cards={
                'top': [None] * 3,
                'middle': [None] * 5,
                'bottom': [None] * 5
            },
            remaining_deck=[],
            current_street=1
        )
        
    def _create_game_state(self, game_state: Dict) -> GameState:
        """Создание состояния игры из словаря"""
        player_cards = [Card(**card) for card in game_state['ai_cards']]
        
        placed_cards = {
            'top': [],
            'middle': [],
            'bottom': []
        }
        
        for row in placed_cards:
            cards = game_state[f'ai_{row}_row']
            placed_cards[row] = [Card(**card) if card else None for card in cards]
            
        return GameState(
            player_cards=player_cards,
            placed_cards=placed_cards,
            remaining_deck=[],
            current_street=game_state['current_street']
        )
        
    def save_progress(self):
        """Сохранение прогресса обучения"""
        progress_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))), 'progress')
            
        if not os.path.exists(progress_dir):
            os.makedirs(progress_dir)
            
        filepath = os.path.join(progress_dir, 'ai_strategy.json')
        self.mccfr.save_progress(filepath)
        
    def load_progress(self):
        """Загрузка прогресса обучения"""
        progress_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))), 'progress')
        filepath = os.path.join(progress_dir, 'ai_strategy.json')
        
        if os.path.exists(filepath):
            self.mccfr = MCCFR.load_progress(filepath)
