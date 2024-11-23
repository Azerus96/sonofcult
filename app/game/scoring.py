from typing import Dict, List
from .player import Player
from .deck import Card
from config import Config

def calculate_score(player: Player, ai: Player) -> Dict:
    """Подсчет очков за игру"""
    scores = {
        'player': {'top': 0, 'middle': 0, 'bottom': 0, 'total': 0, 'bonuses': {}},
        'ai': {'top': 0, 'middle': 0, 'bottom': 0, 'total': 0, 'bonuses': {}}
    }
    
    # Подсчет очков за каждую линию
    for row in ['top', 'middle', 'bottom']:
        player_cards = getattr(player, f"{row}_row")
        ai_cards = getattr(ai, f"{row}_row")
        
        player_combo = player.evaluate_hand(player_cards)
        ai_combo = ai.evaluate_hand(ai_cards)
        
        if player_combo[1] > ai_combo[1]:
            scores['player'][row] = 1
        elif ai_combo[1] > player_combo[1]:
            scores['ai'][row] = 1
    
    # Подсчет бонусов
    scores['player']['bonuses'] = player.calculate_bonuses()
    scores['ai']['bonuses'] = ai.calculate_bonuses()
    
    # Подсчет общего счета
    for player_type in ['player', 'ai']:
        base_score = sum(scores[player_type][row] for row in ['top', 'middle', 'bottom'])
        bonus_score = sum(scores[player_type]['bonuses'].values())
        
        # Бонус за выигрыш всех линий
        if base_score == 3:
            base_score += Config.SCOOP_BONUS
            
        scores[player_type]['total'] = base_score + bonus_score
    
    return scores
