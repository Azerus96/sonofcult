class GameAnimations {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
        this.animationSpeed = 300; // ms
    }

    async dealCard(card, targetElement, delay = 0) {
        return new Promise(resolve => {
            setTimeout(async () => {
                const cardElement = card.cloneNode(true);
                const deckPosition = this._getDeckPosition();
                const targetPosition = this._getElementPosition(targetElement);

                // Устанавливаем начальную позицию
                cardElement.style.position = 'fixed';
                cardElement.style.left = `${deckPosition.x}px`;
                cardElement.style.top = `${deckPosition.y}px`;
                cardElement.style.transform = 'scale(0.8)';
                cardElement.style.opacity = '0';
                cardElement.style.zIndex = '1000';
                cardElement.style.transition = `all ${this.animationSpeed}ms cubic-bezier(0.4, 0, 0.2, 1)`;

                document.body.appendChild(cardElement);

                // Запускаем анимацию
                await this._nextFrame();
                cardElement.style.opacity = '1';
                cardElement.style.transform = 'scale(1)';
                cardElement.style.left = `${targetPosition.x}px`;
                cardElement.style.top = `${targetPosition.y}px`;

                // По завершении анимации
                cardElement.addEventListener('transitionend', () => {
                    cardElement.remove();
                    targetElement.appendChild(card);
                    card.classList.add('card-placed');
                    resolve();
                }, { once: true });
            }, delay);
        });
    }

    async showScore(element, score, isWin) {
        return new Promise(resolve => {
            const scoreElement = document.createElement('div');
            scoreElement.className = `score-animation ${isWin ? 'win' : 'lose'}`;
            scoreElement.textContent = score > 0 ? `+${score}` : score;
            
            // Стили для анимации
            Object.assign(scoreElement.style, {
                position: 'absolute',
                left: '50%',
                transform: 'translateX(-50%) translateY(0)',
                opacity: '0',
                color: isWin ? '#4CAF50' : '#f44336',
                fontSize: '24px',
                fontWeight: 'bold',
                transition: `all ${this.animationSpeed}ms ease-out`
            });

            element.appendChild(scoreElement);

            // Анимация появления и исчезновения
            requestAnimationFrame(() => {
                scoreElement.style.opacity = '1';
                scoreElement.style.transform = 'translateX(-50%) translateY(-20px)';
                
                setTimeout(() => {
                    scoreElement.style.opacity = '0';
                    scoreElement.style.transform = 'translateX(-50%) translateY(-40px)';
                    
                    setTimeout(() => {
                        scoreElement.remove();
                        resolve();
                    }, this.animationSpeed);
                }, this.animationSpeed * 2);
            });
        });
    }

    async highlightCombo(elements, comboType) {
        const colors = {
            'royal_flush': '#FFD700',
            'straight_flush': '#FFA500',
            'four_of_kind': '#FF4500',
            'full_house': '#9370DB',
            'flush': '#20B2AA',
            'straight': '#3CB371',
            'three_of_kind': '#4169E1',
            'two_pairs': '#BA55D3',
            'pair': '#778899'
        };

        const color = colors[comboType] || '#666666';

        return new Promise(resolve => {
            elements.forEach(el => {
                el.style.transition = `all ${this.animationSpeed}ms ease-in-out`;
                el.style.boxShadow = `0 0 15px ${color}`;
                el.style.transform = 'scale(1.05)';
            });

            setTimeout(() => {
                elements.forEach(el => {
                    el.style.boxShadow = 'none';
                    el.style.transform = 'scale(1)';
                });
                setTimeout(resolve, this.animationSpeed);
            }, this.animationSpeed * 2);
        });
    }

    async showFantasy() {
        return new Promise(resolve => {
            const fantasyElement = document.createElement('div');
            fantasyElement.className = 'fantasy-animation';
            
            // Добавляем частицы для эффекта
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.className = 'fantasy-particle';
                particle.style.setProperty('--delay', `${Math.random() * 2}s`);
                particle.style.setProperty('--size', `${Math.random() * 10 + 5}px`);
                fantasyElement.appendChild(particle);
            }

            document.body.appendChild(fantasyElement);

            setTimeout(() => {
                fantasyElement.remove();
                resolve();
            }, 3000);
        });
    }

    async showWinner(isPlayer) {
        return new Promise(resolve => {
            const winnerElement = document.createElement('div');
            winnerElement.className = 'winner-animation';
            winnerElement.textContent = isPlayer ? 'Вы победили!' : 'Победил компьютер';
            
            Object.assign(winnerElement.style, {
                position: 'fixed',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%) scale(0)',
                fontSize: '36px',
                fontWeight: 'bold',
                color: '#4CAF50',
                textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
                transition: `all ${this.animationSpeed}ms ease-out`,
                zIndex: 2000
            });

            document.body.appendChild(winnerElement);

            requestAnimationFrame(() => {
                winnerElement.style.transform = 'translate(-50%, -50%) scale(1)';
                
                setTimeout(() => {
                    winnerElement.style.transform = 'translate(-50%, -50%) scale(0)';
                    setTimeout(() => {
                        winnerElement.remove();
                        resolve();
                    }, this.animationSpeed);
                }, this.animationSpeed * 3);
            });
        });
    }

    _getDeckPosition() {
        // Позиция колоды (центр экрана сверху)
        return {
            x: window.innerWidth / 2 - 35,
            y: -100
        };
    }

    _getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top
        };
    }

    async _nextFrame() {
        return new Promise(resolve => requestAnimationFrame(resolve));
    }

    setAnimationSpeed(speed) {
        this.animationSpeed = speed;
    }
}
