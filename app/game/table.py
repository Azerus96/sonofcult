from typing import Dict, List, Optional, Tuple
from .player import Player
from .deck import Deck, Card
from .scoring import calculate_score
from ..utils.state import save_game_state
import os
from datetime import datetime
import json

class Table:
    def __init__(self):
        self.deck = Deck()
        self.player = Player(is_ai=False)
        self.ai = Player(is_ai=True)
        self.current_street = 0
        self.game_id = None
        self.fantasy_round = False
        self.last_action_time = None
        
    def start_new_game(self) -> Dict:
        """Начало новой игры"""
        self.game_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.deck.reset()
        self.player.reset()
        self.ai.reset()
        self.current_street = 1
        self.fantasy_round = False
        self.last_action_time = datetime.now()
        
        # Раздача первых 5 карт
        player_cards = self.deck.deal(5)
        ai_cards = self.deck.deal(5)
        
        self.player.receive_cards(player_cards)
        self.ai.receive_cards(ai_cards)
        
        self._save_current_state()
        
        return {
            'game_id': self.game_id,
            'player_cards': [card.to_dict() for card in player_cards],
            'current_street': self.current_street
        }

  def next_street(self) -> Optional[Dict]:
        """Переход к следующей улице"""
        if not self._validate_current_street():
            return None
            
        if self.current_street >= 5 and not self.fantasy_round:
            return self._check_fantasy()
            
        if self.current_street >= 5 and self.fantasy_round:
            return self._end_game()
            
        self.current_street += 1
        self.last_action_time = datetime.now()
        
        # Раздача 3 карт на последующих улицах
        player_cards = self.deck.deal(3)
        ai_cards = self.deck.deal(3)
        
        self.player.receive_cards(player_cards)
        self.ai.receive_cards(ai_cards)
        
        # ИИ делает свой ход
        self._ai_move()
        
        self._save_current_state()
        
        return {
            'player_cards': [card.to_dict() for card in player_cards],
            'current_street': self.current_street
        }
        
    def _ai_move(self):
        """Ход ИИ"""
        from ..ai.strategy import AIStrategy
        
        strategy = AIStrategy()
        game_state = self.get_state()
        move = strategy.make_move(game_state)
        
        if move:
            self.ai.place_card(
                Card(**move['card']),
                move['row'],
                move['position']
            )

    def place_card(self, card_data: Dict, row: str, position: int) -> bool:
        """Размещение карты игрока"""
        card = Card(card_data['rank'], card_data['suit'])
        result = self.player.place_card(card, row, position)
        
        if result:
            self.last_action_time = datetime.now()
            self._save_current_state()
            
        return result
        
    def _validate_current_street(self) -> bool:
        """Проверка валидности текущей улицы"""
        # Проверка таймаута
        if self._is_timeout():
            return False
            
        # Проверка правильности размещения карт
        if not self.player.is_valid_placement():
            return False
            
        if not self.ai.is_valid_placement():
            return False
            
        # Проверка количества размещенных карт
        if self.current_street == 1:
            return (len(self.player.current_hand) == 0 and 
                   len(self.ai.current_hand) == 0)
        else:
            return (len(self.player.current_hand) <= 1 and 
                   len(self.ai.current_hand) <= 1)
    
    def _is_timeout(self) -> bool:
        """Проверка таймаута хода"""
        if not self.last_action_time:
            return False
            
        from config import Config
        timeout = datetime.now() - self.last_action_time
        return timeout.total_seconds() > Config.MOVE_TIMEOUT
        
    def _check_fantasy(self) -> Optional[Dict]:
        """Проверка и активация режима фантазии"""
        player_fantasy = self.player.check_fantasy()
        ai_fantasy = self.ai.check_fantasy()
        
        if not player_fantasy and not ai_fantasy:
            return self._end_game()
            
        self.fantasy_round = True
        fantasy_cards = 14  # Базовое количество карт для фантазии
        
        # Определение количества карт для фантазии на основе комбинации
        if player_fantasy:
            top_combo, _ = self.player.evaluate_hand(self.player.top_row)
            if top_combo == 'three_of_kind':
                fantasy_cards = 17
            elif top_combo == 'pair':
                pair_value = max([Card.get_card_value(card) for card in self.player.top_row 
                                if self.player.top_row.count(card) == 2])
                if pair_value == 13:  # KK
                    fantasy_cards = 15
                elif pair_value == 14:  # AA
                    fantasy_cards = 16
                    
        # Раздача карт для фантазии
        self.deck.reset()
        player_cards = self.deck.deal(fantasy_cards if player_fantasy else 0)
        ai_cards = self.deck.deal(fantasy_cards if ai_fantasy else 0)
        
        if player_fantasy:
            self.player.receive_cards(player_cards)
        if ai_fantasy:
            self.ai.receive_cards(ai_cards)
            
        self._save_current_state()
        
        return {
            'fantasy': True,
            'player_fantasy': player_fantasy,
            'ai_fantasy': ai_fantasy,
            'player_cards': [card.to_dict() for card in player_cards] if player_fantasy else [],
            'fantasy_cards': fantasy_cards
        }
        
    def _end_game(self) -> Dict:
        """Завершение игры и подсчет очков"""
        scores = self._calculate_scores()
        self._save_current_state(is_final=True)
        
        return {
            'final': True,
            'scores': scores,
            'player_state': self.player.get_state(),
            'ai_state': self.ai.get_state()
        }
        
    def _calculate_scores(self) -> Dict:
        """Подсчет очков игры"""
        scores = {
            'player': {'top': 0, 'middle': 0, 'bottom': 0, 'total': 0, 'bonuses': {}},
            'ai': {'top': 0, 'middle': 0, 'bottom': 0, 'total': 0, 'bonuses': {}}
        }
        
        # Подсчет очков за каждую линию
        for row in ['top', 'middle', 'bottom']:
            player_cards = getattr(self.player, f"{row}_row")
            ai_cards = getattr(self.ai, f"{row}_row")
            
            player_combo = self.player.evaluate_hand(player_cards)
            ai_combo = self.ai.evaluate_hand(ai_cards)
            
            if player_combo[1] > ai_combo[1]:
                scores['player'][row] = 1
            elif ai_combo[1] > player_combo[1]:
                scores['ai'][row] = 1
                
        # Подсчет бонусов
        scores['player']['bonuses'] = self.player.calculate_bonuses()
        scores['ai']['bonuses'] = self.ai.calculate_bonuses()
        
        # Подсчет общего счета
        for player_type in ['player', 'ai']:
            base_score = sum(scores[player_type][row] for row in ['top', 'middle', 'bottom'])
            bonus_score = sum(scores[player_type]['bonuses'].values())
            
            # Бонус за выигрыш всех линий
            if base_score == 3:
                base_score += 3
                
            scores[player_type]['total'] = base_score + bonus_score
            
        return scores
