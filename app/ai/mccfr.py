import numpy as np
from typing import Dict, List, Tuple, Set
from ..game.deck import Card
import random
from collections import defaultdict
import math

class GameState:
    def __init__(self, player_cards: List[Card], placed_cards: Dict[str, List[Card]], 
                 remaining_deck: List[Card], current_street: int):
        self.player_cards = player_cards
        self.placed_cards = placed_cards
        self.remaining_deck = remaining_deck
        self.current_street = current_street
        
    def to_string(self) -> str:
        """Преобразование состояния в строку"""
        cards_str = [f"{card.rank}{card.suit}" for card in self.player_cards]
        placed_str = []
        for row, cards in self.placed_cards.items():
            placed_str.extend([f"{card.rank}{card.suit}" if card else "00" 
                             for card in cards])
        return f"{self.current_street}|{''.join(cards_str)}|{''.join(placed_str)}"
        
    @classmethod
    def from_string(cls, state_str: str) -> 'GameState':
        """Создание состояния из строки"""
        street, cards, placed = state_str.split('|')
        
        # Восстановление карт в руке
        player_cards = []
        for i in range(0, len(cards), 2):
            if cards[i:i+2] != "00":
                player_cards.append(Card(cards[i], cards[i+1]))
                
        # Восстановление размещенных карт
        placed_cards = {
            'top': [],
            'middle': [],
            'bottom': []
        }
        placed_idx = 0
        for row in ['top', 'middle', 'bottom']:
            limit = 3 if row == 'top' else 5
            for _ in range(limit):
                card_str = placed[placed_idx:placed_idx+2]
                if card_str != "00":
                    placed_cards[row].append(Card(card_str[0], card_str[1]))
                else:
                    placed_cards[row].append(None)
                placed_idx += 2
                
        return cls(player_cards, placed_cards, [], int(street))

class MCCFRNode:
    def __init__(self):
        self.regret_sum = defaultdict(float)
        self.strategy_sum = defaultdict(float)
        self.strategy = defaultdict(float)
        
    def get_strategy(self, reaching_prob: float) -> Dict[str, float]:
        """Получение текущей стратегии"""
        normalizing_sum = 0
        for action in self.regret_sum:
            self.strategy[action] = max(self.regret_sum[action], 0)
            normalizing_sum += self.strategy[action]
            
        for action in self.strategy:
            if normalizing_sum > 0:
                self.strategy[action] /= normalizing_sum
            else:
                self.strategy[action] = 1.0 / len(self.regret_sum)
            self.strategy_sum[action] += reaching_prob * self.strategy[action]
            
        return dict(self.strategy)
        
    def get_average_strategy(self) -> Dict[str, float]:
        """Получение усредненной стратегии"""
        avg_strategy = {}
        normalizing_sum = sum(self.strategy_sum.values())
        
        for action in self.strategy_sum:
            if normalizing_sum > 0:
                avg_strategy[action] = self.strategy_sum[action] / normalizing_sum
            else:
                avg_strategy[action] = 1.0 / len(self.strategy_sum)
                
        return avg_strategy

class MCCFR:
    def __init__(self, exploration_constant: float = 1.5):
        self.nodes = {}
        self.exploration_constant = exploration_constant
        
    def train(self, initial_state: GameState, iterations: int):
        """Обучение агента"""
        for _ in range(iterations):
            self._cfr(initial_state, 1.0)
            
    def _cfr(self, state: GameState, reaching_prob: float) -> float:
        """Рекурсивный CFR"""
        state_str = state.to_string()
        
        if self._is_terminal(state):
            return self._get_utility(state)
            
        if state_str not in self.nodes:
            self.nodes[state_str] = MCCFRNode()
            
        node = self.nodes[state_str]
        strategy = node.get_strategy(reaching_prob)
        
        # Получение возможных действий
        actions = self._get_actions(state)
        if not actions:
            return 0
            
        # Вычисление значения для каждого действия
        action_values = {}
        node_value = 0
        
        for action in actions:
            new_state = self._apply_action(state, action)
            action_values[action] = -self._cfr(new_state, 
                                             reaching_prob * strategy[action])
            node_value += strategy[action] * action_values[action]
            
        # Обновление сожалений
        for action in actions:
            regret = action_values[action] - node_value
            node.regret_sum[action] += reaching_prob * regret
            
        return node_value
        
    def get_action(self, state: GameState) -> str:
        """Получение действия на основе обученной стратегии"""
        state_str = state.to_string()
        if state_str not in self.nodes:
            return random.choice(self._get_actions(state))
            
        strategy = self.nodes[state_str].get_average_strategy()
        return max(strategy.items(), key=lambda x: x[1])[0]
        
    def _is_terminal(self, state: GameState) -> bool:
        """Проверка терминального состояния"""
        if state.current_street >= 5:
            return True
            
        # Проверка заполненности всех линий
        for row, cards in state.placed_cards.items():
            limit = 3 if row == 'top' else 5
            if len([c for c in cards if c]) < limit:
                return False
                
        return True
        
    def _get_utility(self, state: GameState) -> float:
        """Получение полезности терминального состояния"""
        from ..game.player import Player
        
        player = Player()
        player.top_row = [c for c in state.placed_cards['top'] if c]
        player.middle_row = [c for c in state.placed_cards['middle'] if c]
        player.bottom_row = [c for c in state.placed_cards['bottom'] if c]
        
        # Оценка комбинаций
        top_value = player.evaluate_hand(player.top_row)[1]
        middle_value = player.evaluate_hand(player.middle_row)[1]
        bottom_value = player.evaluate_hand(player.bottom_row)[1]
        
        # Штраф за неправильное расположение
        if top_value > middle_value or middle_value > bottom_value:
            return -1000
            
        return top_value + middle_value + bottom_value
        
    def _get_actions(self, state: GameState) -> List[str]:
        """Получение возможных действий"""
        actions = []
        
        for card in state.player_cards:
            for row in ['top', 'middle', 'bottom']:
                limit = 3 if row == 'top' else 5
                placed = state.placed_cards[row]
                
                for pos in range(limit):
                    if not placed[pos]:
                        actions.append(f"{card.rank}{card.suit}_{row}_{pos}")
                        
        return actions
        
    def _apply_action(self, state: GameState, action: str) -> GameState:
        """Применение действия к состоянию"""
        card_str, row, pos = action.split('_')
        pos = int(pos)
        
        # Создание новой карты
        card = Card(card_str[0], card_str[1])
        
        # Копирование состояния
        new_player_cards = [c for c in state.player_cards if c != card]
        new_placed_cards = {
            'top': state.placed_cards['top'].copy(),
            'middle': state.placed_cards['middle'].copy(),
            'bottom': state.placed_cards['bottom'].copy()
        }
        
        # Размещение карты
        new_placed_cards[row][pos] = card
        
        return GameState(
            new_player_cards,
            new_placed_cards,
            state.remaining_deck,
            state.current_street
        )
        
    def serialize(self) -> Dict:
        """Сериализация состояния MCCFR"""
        serialized_nodes = {}
        for state_str, node in self.nodes.items():
            serialized_nodes[state_str] = {
                'regret_sum': dict(node.regret_sum),
                'strategy_sum': dict(node.strategy_sum),
                'strategy': dict(node.strategy)
            }
            
        return {
            'nodes': serialized_nodes,
            'exploration_constant': self.exploration_constant
        }
        
    @classmethod
    def deserialize(cls, data: Dict) -> 'MCCFR':
        """Десериализация состояния MCCFR"""
        mccfr = cls(exploration_constant=data['exploration_constant'])
        
        for state_str, node_data in data['nodes'].items():
            node = MCCFRNode()
            node.regret_sum = defaultdict(float, node_data['regret_sum'])
            node.strategy_sum = defaultdict(float, node_data['strategy_sum'])
            node.strategy = defaultdict(float, node_data['strategy'])
            mccfr.nodes[state_str] = node
            
        return mccfr
        
    def save_progress(self, filepath: str):
        """Сохранение прогресса обучения"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.serialize(), f)
            
    @classmethod
    def load_progress(cls, filepath: str) -> 'MCCFR':
        """Загрузка прогресса обучения"""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.deserialize(data)
        
    def update_strategy(self, state: GameState, action: str, reward: float):
        """Обновление стратегии на основе полученного вознаграждения"""
        state_str = state.to_string()
        if state_str not in self.nodes:
            self.nodes[state_str] = MCCFRNode()
            
        node = self.nodes[state_str]
        
        # Обновление сожалений и стратегии
        actions = self._get_actions(state)
        current_value = node.strategy.get(action, 1.0 / len(actions))
        
        # Обновление с использованием UCB1
        exploration_term = math.sqrt(
            (2 * math.log(sum(node.strategy_sum.values()) + 1)) /
            (node.strategy_sum.get(action, 0) + 1)
        )
        
        new_value = current_value + reward + self.exploration_constant * exploration_term
        
        node.regret_sum[action] += new_value - current_value
        node.strategy_sum[action] += 1
        
        # Пересчет стратегии
        node.get_strategy(1.0)
