class CardDeck {
    constructor() {
        this.suits = ['hearts', 'diamonds', 'clubs', 'spades'];
        this.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
        this.suitSymbols = {
            'hearts': '♥',
            'diamonds': '♦',
            'clubs': '♣',
            'spades': '♠'
        };
        this.suitColors = {
            'hearts': '#ff0000',
            'diamonds': '#ff0000',
            'clubs': '#000000',
            'spades': '#000000'
        };
    }

    createCardElement(card) {
        const element = document.createElement('div');
        element.className = 'card';
        element.dataset.rank = card.rank;
        element.dataset.suit = card.suit;

        // SVG разметка для карты
        const svg = `
            <svg width="70" height="100" viewBox="0 0 70 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <filter id="shadow">
                        <feDropShadow dx="1" dy="1" stdDeviation="1" flood-opacity="0.3"/>
                    </filter>
                </defs>
                <rect width="66" height="96" x="2" y="2" rx="5" ry="5" 
                      fill="white" stroke="#ccc" stroke-width="1" filter="url(#shadow)"/>
                <text x="5" y="20" font-size="16" fill="${this.suitColors[card.suit]}"
                      font-family="Arial" font-weight="bold">${card.rank}</text>
                <text x="5" y="40" font-size="20" fill="${this.suitColors[card.suit]}"
                      font-family="Arial">${this.suitSymbols[card.suit]}</text>
                <text x="35" y="60" font-size="30" fill="${this.suitColors[card.suit]}"
                      font-family="Arial">${this.suitSymbols[card.suit]}</text>
                <text x="65" y="95" font-size="16" fill="${this.suitColors[card.suit]}"
                      font-family="Arial" font-weight="bold" text-anchor="end">${card.rank}</text>
            </svg>
        `;

        element.innerHTML = svg;
        this.makeCardDraggable(element);
        return element;
    }

    makeCardDraggable(cardElement) {
        cardElement.draggable = true;

        // Desktop drag events
        cardElement.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', 
                JSON.stringify({
                    rank: cardElement.dataset.rank,
                    suit: cardElement.dataset.suit
                })
            );
            cardElement.classList.add('dragging');
            
            // Создаем превью для перетаскивания
            const dragImage = cardElement.cloneNode(true);
            dragImage.style.position = 'absolute';
            dragImage.style.top = '-1000px';
            document.body.appendChild(dragImage);
            e.dataTransfer.setDragImage(dragImage, 35, 50);
            setTimeout(() => dragImage.remove(), 0);
        });

        cardElement.addEventListener('dragend', () => {
            cardElement.classList.remove('dragging');
        });

        // Mobile touch events
        let initialX, initialY, currentX, currentY;
        let xOffset = 0;
        let yOffset = 0;
        let active = false;

        cardElement.addEventListener('touchstart', (e) => {
            initialX = e.touches[0].clientX - xOffset;
            initialY = e.touches[0].clientY - yOffset;

            if (e.target === cardElement) {
                active = true;
                cardElement.classList.add('dragging');
            }
        });

        cardElement.addEventListener('touchmove', (e) => {
            if (active) {
                e.preventDefault();

                currentX = e.touches[0].clientX - initialX;
                currentY = e.touches[0].clientY - initialY;

                xOffset = currentX;
                yOffset = currentY;

                cardElement.style.transform = 
                    `translate3d(${currentX}px, ${currentY}px, 0)`;

                // Находим слот под пальцем
                const touch = e.touches[0];
                const slot = document.elementFromPoint(touch.clientX, touch.clientY);

                // Подсвечиваем доступный слот
                document.querySelectorAll('.card-slot').forEach(s => 
                    s.classList.remove('highlight'));
                if (slot && slot.classList.contains('card-slot')) {
                    slot.classList.add('highlight');
                }
            }
        });

        cardElement.addEventListener('touchend', (e) => {
            if (!active) return;

            const touch = e.changedTouches[0];
            const slot = document.elementFromPoint(touch.clientX, touch.clientY);

            if (slot && slot.classList.contains('card-slot')) {
                const cardData = {
                    rank: cardElement.dataset.rank,
                    suit: cardElement.dataset.suit
                };

                // Вызываем событие размещения карты
                const event = new CustomEvent('cardPlaced', {
                    detail: {
                        card: cardData,
                        row: slot.dataset.row,
                        position: parseInt(slot.dataset.position)
                    }
                });
                document.dispatchEvent(event);
            }

            // Сброс стилей
            cardElement.style.transform = '';
            cardElement.classList.remove('dragging');
            document.querySelectorAll('.card-slot').forEach(s => 
                s.classList.remove('highlight'));

            active = false;
            xOffset = 0;
            yOffset = 0;
        });
    }

    getCardValue(rank) {
        const values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
            '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        };
        return values[rank];
    }

    compareCards(card1, card2) {
        const value1 = this.getCardValue(card1.rank);
        const value2 = this.getCardValue(card2.rank);
        
        if (value1 !== value2) {
            return value1 - value2;
        }
        
        // Если значения равны, сравниваем масти
        const suitOrder = {'spades': 3, 'hearts': 2, 'diamonds': 1, 'clubs': 0};
        return suitOrder[card1.suit] - suitOrder[card2.suit];
    }
}
