document.addEventListener('DOMContentLoaded', () => {
    // Only run if we are on the main swiping page
    if (!document.getElementById('card-container')) return;

    let users = [];
    let currentIndex = 0;
    const cardContainer = document.getElementById('card-container');
    const loading = document.querySelector('.loading');
    const controls = document.getElementById('controls');

    // Fetch potential matches
    fetch('/api/users')
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch users');
            return response.json();
        })
        .then(data => {
            users = data;
            loading.classList.add('hidden');
            if (users.length > 0) {
                renderCard();
                controls.classList.remove('hidden');
            } else {
                cardContainer.innerHTML = '<div class="no-matches">No more users to swipe!</div>';
            }
        })
        .catch(err => {
            console.error(err);
            loading.innerText = 'Error loading users';
        });

    function renderCard() {
        if (currentIndex >= users.length) {
            cardContainer.innerHTML = '<div class="no-matches">No more users to swipe!</div>';
            controls.classList.add('hidden');
            return;
        }

        const user = users[currentIndex];
        const card = document.createElement('div');
        card.className = 'card';
        card.style.backgroundImage = `url(${user.image_url || 'https://via.placeholder.com/300x400'})`;

        const info = document.createElement('div');
        info.className = 'card-info';
        info.innerHTML = `<h3>${user.username}</h3><p>${user.bio || 'No bio'}</p>`;

        card.appendChild(info);
        cardContainer.innerHTML = '';
        cardContainer.appendChild(card);
    }

    // Swipe actions
    document.getElementById('nope').addEventListener('click', () => handleSwipe(false));
    document.getElementById('like').addEventListener('click', () => handleSwipe(true));

    function handleSwipe(isLike) {
        if (currentIndex >= users.length) return;

        const user = users[currentIndex];
        const card = document.querySelector('.card');

        // Visual feedback
        card.style.transform = `translateX(${isLike ? '200%' : '-200%'}) rotate(${isLike ? '20deg' : '-20deg'})`;
        card.style.opacity = '0';

        // Send to API
        fetch('/api/swipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                swiped_id: user.id,
                is_like: isLike
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Swipe failed');
            return response.json();
        })
        .then(data => {
            if (data.match) {
                showMatchModal(user);
            }
        })
        .catch(err => console.error(err));

        currentIndex++;
        setTimeout(() => {
            renderCard();
        }, 300);
    }

    function showMatchModal(user) {
        const modal = document.getElementById('match-modal');
        document.getElementById('matched-user-name').textContent = user.username;
        document.getElementById('matched-user-img').src = user.image_url || 'https://via.placeholder.com/150';
        modal.classList.remove('hidden');
    }

    document.getElementById('close-modal').addEventListener('click', () => {
        document.getElementById('match-modal').classList.add('hidden');
    });

    // Matches Panel
    const matchesLink = document.getElementById('matches-link');
    const matchesPanel = document.getElementById('matches-panel');
    const closeMatches = document.getElementById('close-matches');

    if (matchesLink) {
        matchesLink.addEventListener('click', (e) => {
            e.preventDefault();
            loadMatches();
            matchesPanel.classList.remove('hidden');
        });
    }

    if (closeMatches) {
        closeMatches.addEventListener('click', () => {
            matchesPanel.classList.add('hidden');
        });
    }

    function loadMatches() {
        fetch('/api/matches')
            .then(response => response.json())
            .then(matches => {
                const list = document.getElementById('matches-list');
                if (matches.length === 0) {
                    list.innerHTML = '<li>No matches yet.</li>';
                    return;
                }
                list.innerHTML = matches.map(match => `
                    <li>
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <img src="${match.user.image_url || 'https://via.placeholder.com/50'}" style="width: 40px; height: 40px; border-radius: 50%;">
                            <span>${match.user.username}</span>
                        </div>
                    </li>
                `).join('');
            });
    }
});
