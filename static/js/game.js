class ChinesePoker {
    constructor() {
        this.deck = new CardDeck();
        this.animations = new GameAnimations();
        this.gameState = {
            currentStreet: 0,
            gameId: null,
            playerCards: [],
            placedCards: {
                top: Array(3).fill(null),
                middle: Array(5).fill(null),
                bottom: Array(5).fill(null)
            },
            timer: 30,
            timerInterval: null
        };

        this.initializeElements();
        this.attachEventListeners();
        this.loadGameState();
    }

    initializeElements() {
        this.elements = {
            startBtn: document.getElementById('start-btn'),
            okBtn: document.getElementById('ok-btn'),
            playerHand: document.querySelector('.player-hand'),
            playerTable: document.querySelector('.player-table'),
            aiTable: document.querySelector('.ai-table'),
            scoring: document.querySelector('.scoring'),
            loader: document.getElementById('loader'),
            timer: document.getElementById('timer'),
            currentStreet: document.getElementById('current-street'),
            fantasyModal: document.getElementById('fantasy-modal'),
            toastContainer: document.getElementById('toast-container')
        };

        this.cardSlots = {
            top: Array.from(document.querySelectorAll('.player-table .top-row .card-slot')),
            middle: Array.from(document.querySelectorAll('.player-table .middle-row .card-slot')),
            bottom: Array.from(document.querySelectorAll('.player-table .bottom-row .card-slot'))
        };
    }

    attachEventListeners() {
        this.elements.startBtn.addEventListener('click', () => this.startGame());
        this.elements.okBtn.addEventListener('click', () => this.nextStreet());

        // Обработчики для слотов карт
        Object.values(this.cardSlots).flat().forEach(slot => {
            slot.addEventListener('dragover', e => {
                e.preventDefault();
                if (this.canPlaceCard(slot)) {
                    slot.classList.add('highlight');
                }
            });

            slot.addEventListener('dragleave', () => {
                slot.classList.remove('highlight');
            });

            slot.addEventListener('drop', e => this.handleCardDrop(e, slot));
        });

        // Обработчик размещения карты (для мобильных устройств)
        document.addEventListener('cardPlaced', (e) => {
            const { card, row, position } = e.detail;
            this.placeCard(card, row, position);
        });

        // Обработчики для модального окна фантазии
        document.getElementById('fantasy-yes').addEventListener('click', () => {
            this.elements.fantasyModal.style.display = 'none';
            this.startFantasy();
        });

        document.getElementById('fantasy-no').addEventListener('click', () => {
            this.elements.fantasyModal.style.display = 'none';
            this.endGame();
        });

        // Сохранение состояния перед закрытием страницы
        window.addEventListener('beforeunload', () => this.saveGameState());

        // Обработчик изменения видимости страницы
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseTimer();
            } else {
                this.resumeTimer();
            }
        });
    }

    async startGame() {
        try {
            this.showLoader();
            const response = await fetch('/api/start', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to start game');
            }

            this.gameState.gameId = data.game_id;
            this.gameState.currentStreet = 1;
            this.elements.currentStreet.textContent = '1';
            
            // Очистка столов
            this.clearTables();
            
            // Раздача начальных карт
            await this.dealInitialCards(data.player_cards);
            
            this.elements.okBtn.disabled = false;
            this.elements.startBtn.disabled = true;

            // Запуск таймера
            this.startTimer();

            this.showToast('Игра началась!', 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
            console.error('Error starting game:', error);
        } finally {
            this.hideLoader();
        }
    }

    async nextStreet() {
        if (!this.validateCurrentPlacement()) {
            this.showToast('Разместите все карты правильно', 'warning');
            return;
        }

        try {
            this.showLoader();
            const response = await fetch('/api/next', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to proceed to next street');
            }

            if (data.final) {
                await this.showFinalScores(data.scores);
            } else if (data.fantasy) {
                this.handleFantasy(data);
            } else {
                this.gameState.currentStreet++;
                this.elements.currentStreet.textContent = this.gameState.currentStreet;
                await this.dealStreetCards(data.player_cards);
                this.resetTimer();
            }
        } catch (error) {
            this.showToast(error.message, 'error');
            console.error('Error in next street:', error);
        } finally {
            this.hideLoader();
        }
    }

    async dealInitialCards(cards) {
        this.gameState.playerCards = cards;
        
        for (const card of cards) {
            const cardElement = this.deck.createCardElement(card);
            await this.animations.dealCard(cardElement, this.elements.playerHand, 100);
        }
    }

    async dealStreetCards(cards) {
        for (const card of cards) {
            const cardElement = this.deck.createCardElement(card);
            await this.animations.dealCard(cardElement, this.elements.playerHand, 100);
        }
    }

    async placeCard(cardData, row, position) {
        try {
            const response = await fetch('/api/place', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ card: cardData, row, position })
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to place card');
            }

            if (result.success) {
                this.gameState.placedCards[row][position] = cardData;
                return true;
            }
            return false;
        } catch (error) {
            this.showToast(error.message, 'error');
            return false;
        }
    }

    handleCardDrop(e, slot) {
        e.preventDefault();
        slot.classList.remove('highlight');

        if (!this.canPlaceCard(slot)) {
            return;
        }

        const cardData = JSON.parse(e.dataTransfer.getData('text/plain'));
        
        this.placeCard(cardData, slot.dataset.row, parseInt(slot.dataset.position))
            .then(success => {
                if (success) {
                    const cardElement = this.deck.createCardElement(cardData);
                    slot.appendChild(cardElement);
                    this.removeCardFromHand(cardData);
                    this.checkCompletion();
                }
            });
    }

    canPlaceCard(slot) {
        // Проверка возможности размещения карты
        if (!slot.dataset.row || slot.children.length > 0) {
            return false;
        }

        const row = slot.dataset.row;
        const position = parseInt(slot.dataset.position);
        
        // Проверка лимитов для каждого ряда
        const rowLimits = {
            'top': 3,
            'middle': 5,
            'bottom': 5
        };

        const currentRowCards = this.gameState.placedCards[row].filter(card => card !== null);
        return currentRowCards.length < rowLimits[row];
    }

    removeCardFromHand(cardData) {
        const cardElement = Array.from(this.elements.playerHand.children)
            .find(el => el.dataset.rank === cardData.rank && 
                       el.dataset.suit === cardData.suit);
        if (cardElement) {
            cardElement.remove();
        }
    }

    checkCompletion() {
        const cardsPlaced = {
            top: this.gameState.placedCards.top.filter(card => card !== null).length,
            middle: this.gameState.placedCards.middle.filter(card => card !== null).length,
            bottom: this.gameState.placedCards.bottom.filter(card => card !== null).length
        };

        if (this.gameState.currentStreet === 1) {
            if (cardsPlaced.top + cardsPlaced.middle + cardsPlaced.bottom === 5) {
                this.elements.okBtn.disabled = false;
            }
        } else {
            if (cardsPlaced.top + cardsPlaced.middle + cardsPlaced.bottom === 2) {
                this.elements.okBtn.disabled = false;
            }
        }
    }

    validateCurrentPlacement() {
        // Проверка правильности размещения карт
        const placement = this.gameState.placedCards;
        
        // Проверка количества карт
        const countCards = (row) => row.filter(card => card !== null).length;
        
        if (this.gameState.currentStreet === 1) {
            if (countCards(placement.top) + 
                countCards(placement.middle) + 
                countCards(placement.bottom) !== 5) {
                return false;
            }
        } else {
            if (countCards(placement.top) + 
                countCards(placement.middle) + 
                countCards(placement.bottom) !== 2) {
                return false;
            }
        }

        // Проверка силы комбинаций
        const getHandStrength = (cards) => {
            if (cards.filter(card => card !== null).length === 0) return 0;
            return this.evaluateHand(cards.filter(card => card !== null));
        };

        const topStrength = getHandStrength(placement.top);
        const middleStrength = getHandStrength(placement.middle);
        const bottomStrength = getHandStrength(placement.bottom);

        return topStrength <= middleStrength && middleStrength <= bottomStrength;
    }

    evaluateHand(cards) {
        // Оценка силы комбинации
        const values = cards.map(card => this.deck.getCardValue(card.rank));
        const suits = cards.map(card => card.suit);
        
        // Подсчет количества карт каждого достоинства и масти
        const valueCounts = {};
        const suitCounts = {};
        
        values.forEach(value => {
            valueCounts[value] = (valueCounts[value] || 0) + 1;
        });
        
        suits.forEach(suit => {
            suitCounts[suit] = (suitCounts[suit] || 0) + 1;
        });

        // Проверка комбинаций от старшей к младшей
        if (this.isRoyalFlush(values, suits)) return 1000;
        if (this.isStraightFlush(values, suits)) return 900;
        if (this.isFourOfKind(valueCounts)) return 800;
        if (this.isFullHouse(valueCounts)) return 700;
        if (this.isFlush(suitCounts)) return 600;
        if (this.isStraight(values)) return 500;
        if (this.isThreeOfKind(valueCounts)) return 400;
        if (this.isTwoPairs(valueCounts)) return 300;
        if (this.isPair(valueCounts)) return 200;
        
        return Math.max(...values);
    }

    isRoyalFlush(values, suits) {
        return this.isStraightFlush(values, suits) && 
               values.includes(14) && values.includes(13);
    }

    isStraightFlush(values, suits) {
        return this.isFlush(suits) && this.isStraight(values);
    }

    isFourOfKind(valueCounts) {
        return Object.values(valueCounts).includes(4);
    }

    isFullHouse(valueCounts) {
        const counts = Object.values(valueCounts);
        return counts.includes(3) && counts.includes(2);
    }

    isFlush(suitCounts) {
        return Object.values(suitCounts).some(count => count >= 5);
    }

    isStraight(values) {
        const uniqueValues = [...new Set(values)].sort((a, b) => a - b);
        
        // Проверка обычного стрита
        for (let i = 0; i < uniqueValues.length - 4; i++) {
            if (uniqueValues[i + 4] - uniqueValues[i] === 4) {
                return true;
            }
        }
        
        // Проверка стрита с тузом внизу (A,2,3,4,5)
        if (uniqueValues.includes(14)) {
            const lowAceValues = uniqueValues
                .map(v => v === 14 ? 1 : v)
                .sort((a, b) => a - b);
            
            for (let i = 0; i < lowAceValues.length - 4; i++) {
                if (lowAceValues[i + 4] - lowAceValues[i] === 4) {
                    return true;
                }
            }
        }
        
        return false;
    }

    isThreeOfKind(valueCounts) {
        return Object.values(valueCounts).includes(3);
    }

    isTwoPairs(valueCounts) {
        return Object.values(valueCounts).filter(count => count === 2).length === 2;
    }

    isPair(valueCounts) {
        return Object.values(valueCounts).includes(2);
    }

    async showFinalScores(scores) {
        this.elements.scoring.style.display = 'block';
        
        // Анимация подсчета очков
        const rows = ['top', 'middle', 'bottom'];
        for (const row of rows) {
            await this.animations.showScore(
                document.getElementById(`${row}-score-player`),
                scores.player[row],
                scores.player[row] > scores.ai[row]
            );
            
            await this.animations.showScore(
                document.getElementById(`${row}-score-ai`),
                scores.ai[row],
                scores.ai[row] > scores.player[row]
            );
        }

        // Показ общего счета
        await this.animations.showScore(
            document.getElementById('total-score-player'),
            scores.player.total,
            scores.player.total > scores.ai.total
        );
        
        await this.animations.showScore(
            document.getElementById('total-score-ai'),
            scores.ai.total,
            scores.ai.total > scores.player.total
        );

        // Показ победителя
        await this.animations.showWinner(scores.player.total > scores.ai.total);

        this.elements.okBtn.disabled = true;
        this.elements.startBtn.disabled = false;
        this.stopTimer();
    }

    handleFantasy(data) {
        if (data.player_fantasy || data.ai_fantasy) {
            this.elements.fantasyModal.style.display = 'block';
            this.stopTimer();
        }
    }

    async startFantasy() {
        try {
            this.showLoader();
            const response = await fetch('/api/fantasy', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to start fantasy');
            }

            // Очистка столов
            this.clearTables();
            
            // Раздача карт для фантазии
            if (data.player_cards.length > 0) {
                await this.animations.showFantasy();
                await this.dealFantasyCards(data.player_cards);
            }

            this.startTimer();
        } catch (error) {
            this.showToast(error.message, 'error');
            console.error('Error in fantasy:', error);
        } finally {
            this.hideLoader();
        }
    }

    async dealFantasyCards(cards) {
        for (const card of cards) {
            const cardElement = this.deck.createCardElement(card);
            await this.animations.dealCard(cardElement, this.elements.playerHand, 50);
        }
    }

    startTimer() {
        this.gameState.timer = 30;
        this.elements.timer.textContent = this.gameState.timer;
        
        this.gameState.timerInterval = setInterval(() => {
            this.gameState.timer--;
            this.elements.timer.textContent = this.gameState.timer;
            
            if (this.gameState.timer <= 5) {
                this.elements.timer.classList.add('warning');
            }
            
            if (this.gameState.timer <= 0) {
                this.stopTimer();
                this.autoComplete();
            }
        }, 1000);
    }

    stopTimer() {
        if (this.gameState.timerInterval) {
            clearInterval(this.gameState.timerInterval);
            this.gameState.timerInterval = null;
        }
        this.elements.timer.classList.remove('warning');
    }

    pauseTimer() {
        this.stopTimer();
    }

    resumeTimer() {
        if (this.gameState.currentStreet > 0) {
            this.startTimer();
        }
    }

    resetTimer() {
        this.stopTimer();
        this.startTimer();
    }

    autoComplete() {
        // Автоматическое размещение оставшихся карт
        const remainingCards = Array.from(this.elements.playerHand.children);
        const emptySlots = Object.values(this.cardSlots)
            .flat()
            .filter(slot => !slot.children.length);

        remainingCards.forEach((card, index) => {
            if (emptySlots[index]) {
                const cardData = {
                    rank: card.dataset.rank,
                    suit: card.dataset.suit
                };
                this.placeCard(
                    cardData,
                    emptySlots[index].dataset.row,
                    parseInt(emptySlots[index].dataset.position)
                );
            }
        });

        this.nextStreet();
    }

    showLoader() {
        this.elements.loader.style.display = 'flex';
    }

    hideLoader() {
        this.elements.loader.style.display = 'none';
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        this.elements.toastContainer.appendChild(toast);

        // Анимация появления
        requestAnimationFrame(() => {
            toast.classList.add('show');
            
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        });
    }

    clearTables() {
        // Очистка стола игрока
        Object.values(this.cardSlots).flat().forEach(slot => {
            while (slot.firstChild) {
                slot.firstChild.remove();
            }
        });

        // Очистка руки игрока
        while (this.elements.playerHand.firstChild) {
            this.elements.playerHand.firstChild.remove();
        }

        // Очистка стола ИИ
        Array.from(this.elements.aiTable.querySelectorAll('.card-slot')).forEach(slot => {
            while (slot.firstChild) {
                slot.firstChild.remove();
            }
        });

        // Сброс состояния
        this.gameState.placedCards = {
            top: Array(3).fill(null),
            middle: Array(5).fill(null),
            bottom: Array(5).fill(null)
        };

        // Скрытие результатов
        this.elements.scoring.style.display = 'none';
    }

    saveGameState() {
        localStorage.setItem('gameState', JSON.stringify({
            ...this.gameState,
            timerInterval: null // Не сохраняем интервал
        }));
    }

    loadGameState() {
        const savedState = localStorage.getItem('gameState');
        if (savedState) {
            const state = JSON.parse(savedState);
            if (state.gameId) {
                fetch(`/api/load/${state.gameId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.restoreGameState(data.state);
                        }
                    })
                    .catch(console.error);
            }
        }
    }

    restoreGameState(state) {
        this.gameState = state;
        this.clearTables();
        
        // Восстановление размещенных карт
        Object.entries(state.placedCards).forEach(([row, cards]) => {
            cards.forEach((card, index) => {
                if (card) {
                    const cardElement = this.deck.createCardElement(card);
                    this.cardSlots[row][index].appendChild(cardElement);
                }
            });
        });

        // Восстановление карт в руке
        state.playerCards.forEach(card => {
            const cardElement = this.deck.createCardElement(card);
            this.elements.playerHand.appendChild(cardElement);
        });

        // Обновление UI
        this.elements.currentStreet.textContent = state.currentStreet;
        this.elements.startBtn.disabled = state.currentStreet > 0;
        this.elements.okBtn.disabled = state.currentStreet === 0;

        if (state.currentStreet > 0) {
            this.startTimer();
        }
    }
}

// Инициализация игры при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.game = new ChinesePoker();
});
