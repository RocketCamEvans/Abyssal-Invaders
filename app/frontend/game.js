// Abyssal Invaders - Game Logic

// Game State
const gameState = {
    sessionId: null,
    player: null,
    currentRoom: null,
    inCombat: false,
    currentEnemy: null,
    currentAlly: null
};

// API Base URL
const API_BASE = '/api';

// DOM Elements
let elements = {};

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
    showScreen('start-screen');
    loadLeaderboard();
});

// Initialize DOM element references
function initializeElements() {
    elements = {
        // Screens
        startScreen: document.getElementById('start-screen'),
        gameScreen: document.getElementById('game-screen'),
        gameOverScreen: document.getElementById('game-over-screen'),
        
        // Start screen
        playerNameInput: document.getElementById('player-name'),
        startGameBtn: document.getElementById('start-game-btn'),
        viewLeaderboardBtn: document.getElementById('view-leaderboard-btn'),
        
        // Player info
        playerNameDisplay: document.getElementById('player-name-display'),
        healthBar: document.getElementById('health-bar'),
        healthText: document.getElementById('health-text'),
        playerGold: document.getElementById('player-gold'),
        playerLevel: document.getElementById('player-level'),
        playerFloor: document.getElementById('player-floor'),
        playerAllies: document.getElementById('player-allies'),
        playerAttack: document.getElementById('player-attack'),
        playerDefense: document.getElementById('player-defense'),
        
        // Room display
        roomName: document.getElementById('room-name'),
        roomDescription: document.getElementById('room-description'),
        roomFeatures: document.getElementById('room-features'),
        
        // Combat
        combatArea: document.getElementById('combat-area'),
        enemyName: document.getElementById('enemy-name'),
        enemyDescription: document.getElementById('enemy-description'),
        enemyHealthBar: document.getElementById('enemy-health-bar'),
        enemyHealthText: document.getElementById('enemy-health-text'),
        enemyAttack: document.getElementById('enemy-attack'),
        enemyDefense: document.getElementById('enemy-defense'),
        attackBtn: document.getElementById('attack-btn'),
        useAllyBtn: document.getElementById('use-ally-btn'),
        useItemBtn: document.getElementById('use-item-btn'),
        fleeBtn: document.getElementById('flee-btn'),
        
        // Event log
        eventLog: document.getElementById('event-log'),
        
        // Movement
        moveNorth: document.getElementById('move-north'),
        moveSouth: document.getElementById('move-south'),
        moveEast: document.getElementById('move-east'),
        moveWest: document.getElementById('move-west'),
        moveUp: document.getElementById('move-up'),
        
        // Actions
        viewStatsBtn: document.getElementById('view-stats-btn'),
        viewScoresBtn: document.getElementById('view-scores-btn'),
        submitScoreBtn: document.getElementById('submit-score-btn'),
        newGameBtn: document.getElementById('new-game-btn'),
        
        // Allies
        alliesList: document.getElementById('allies-list'),
        
        // Inventory
        inventoryList: document.getElementById('inventory-list'),
        
        // Leaderboard
        leaderboardList: document.getElementById('leaderboard-list'),
        
        // Game over
        finalGold: document.getElementById('final-gold'),
        finalLevel: document.getElementById('final-level'),
        finalFloor: document.getElementById('final-floor'),
        finalAllies: document.getElementById('final-allies'),
        submitFinalScoreBtn: document.getElementById('submit-final-score-btn'),
        restartGameBtn: document.getElementById('restart-game-btn'),
        viewFinalLeaderboardBtn: document.getElementById('view-final-leaderboard-btn'),
        
        // Modals
        leaderboardModal: document.getElementById('leaderboard-modal'),
        statsModal: document.getElementById('stats-modal'),
        itemModal: document.getElementById('item-modal'),
        modalLeaderboardList: document.getElementById('modal-leaderboard-list'),
        modalStatsContent: document.getElementById('modal-stats-content'),
        modalItemList: document.getElementById('modal-item-list')
    };
}

// Attach event listeners
function attachEventListeners() {
    // Start game
    elements.startGameBtn.addEventListener('click', startNewGame);
    elements.playerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startNewGame();
    });
    
    // Movement
    elements.moveNorth.addEventListener('click', () => movePlayer('north'));
    elements.moveSouth.addEventListener('click', () => movePlayer('south'));
    elements.moveEast.addEventListener('click', () => movePlayer('east'));
    elements.moveWest.addEventListener('click', () => movePlayer('west'));
    elements.moveUp.addEventListener('click', () => movePlayer('up'));
    
    // Combat
    elements.attackBtn.addEventListener('click', () => performCombatAction('attack', false));
    elements.useAllyBtn.addEventListener('click', () => performCombatAction('attack', true));
    elements.useItemBtn.addEventListener('click', () => showItemModal());
    elements.fleeBtn.addEventListener('click', () => performCombatAction('flee', false));
    
    // Actions
    elements.viewStatsBtn.addEventListener('click', viewStats);
    elements.viewScoresBtn.addEventListener('click', () => showLeaderboardModal());
    elements.submitScoreBtn.addEventListener('click', submitScore);
    elements.newGameBtn.addEventListener('click', confirmNewGame);
    elements.viewLeaderboardBtn.addEventListener('click', () => showLeaderboardModal());
    
    // Game over
    elements.submitFinalScoreBtn.addEventListener('click', submitScore);
    elements.restartGameBtn.addEventListener('click', () => {
        showScreen('start-screen');
        resetGameState();
    });
    elements.viewFinalLeaderboardBtn.addEventListener('click', () => showLeaderboardModal());
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').classList.remove('active');
        });
    });
    
    // Close modals on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// API Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        addLogEntry(`Error: ${error.message}`, 'danger');
        return { error: true, message: error.message };
    }
}

// Start new game
async function startNewGame() {
    const playerName = elements.playerNameInput.value.trim() || 'Adventurer';
    
    addLogEntry('Starting new adventure...', 'important');
    
    const result = await apiRequest('/player/new', 'POST', { name: playerName });
    
    if (result.error) {
        addLogEntry(`Failed to start game: ${result.message}`, 'danger');
        return;
    }
    
    gameState.sessionId = result.data.session_id;
    gameState.player = result.data.player;
    gameState.currentRoom = result.data.current_room;
    
    // Initialize player fields if not present
    if (!gameState.player.allies_count) gameState.player.allies_count = 0;
    if (!gameState.player.level) gameState.player.level = 1;
    if (!gameState.player.attack_power) gameState.player.attack_power = 10;
    if (!gameState.player.defense) gameState.player.defense = 5;
    if (!gameState.player.inventory) gameState.player.inventory = [];
    
    // Load inventory from API if provided
    if (result.data.player.inventory) {
        gameState.player.inventory = result.data.player.inventory;
    }
    
    showScreen('game-screen');
    updatePlayerDisplay();
    updateRoomDisplay();
    addLogEntry(result.message || 'Welcome to Abyssal Invaders!', 'success');
    addLogEntry(gameState.currentRoom.description);
    
    loadLeaderboard();
}

// Update player display
function updatePlayerDisplay() {
    if (!gameState.player) return;
    
    elements.playerNameDisplay.textContent = gameState.player.name;
    
    // Parse health string "50/100"
    const healthParts = gameState.player.health.split('/');
    const currentHealth = parseInt(healthParts[0]);
    const maxHealth = parseInt(healthParts[1]);
    const healthPercent = (currentHealth / maxHealth) * 100;
    
    elements.healthBar.style.width = `${healthPercent}%`;
    elements.healthText.textContent = gameState.player.health;
    
    elements.playerGold.textContent = gameState.player.gold;
    elements.playerLevel.textContent = gameState.player.level || 1;
    elements.playerFloor.textContent = gameState.player.floor;
    elements.playerAllies.textContent = gameState.player.allies_count || 0;
    elements.playerAttack.textContent = gameState.player.attack_power || 10;
    elements.playerDefense.textContent = gameState.player.defense || 5;
    
    // Update allies list
    updateAlliesList();
    
    // Update inventory display
    updateInventoryDisplay();
}

// Update allies list
function updateAlliesList() {
    const alliesList = elements.alliesList;
    
    if (!gameState.player || !gameState.player.allies_count || gameState.player.allies_count === 0) {
        alliesList.innerHTML = '<p class="empty-state">No allies recruited yet</p>';
        return;
    }
    
    // Note: The API doesn't return full ally details in player object
    // This is a placeholder - in a real scenario, you'd fetch this data
    alliesList.innerHTML = `<p class="ally-item">You have ${gameState.player.allies_count} ally(ies) ready to assist you in battle!</p>`;
}

// Update inventory display
function updateInventoryDisplay() {
    const inventoryList = elements.inventoryList;
    
    if (!gameState.player || !gameState.player.inventory || gameState.player.inventory.length === 0) {
        inventoryList.innerHTML = '<p class="empty-state">No items yet</p>';
        return;
    }
    
    inventoryList.innerHTML = gameState.player.inventory.map(item => {
        const rarityEmoji = {
            'common': '⚪',
            'uncommon': '🟢',
            'rare': '🔵',
            'epic': '🟣',
            'legendary': '🟡'
        };
        
        // Create detailed tooltip text
        const tooltipText = `${item.description || item.name}\n\nEffect: ${item.effect_type || 'unknown'}\nValue: ${item.effect_value || 0}\nRarity: ${item.rarity || 'common'}${item.usable_in_combat ? '\n✓ Can use in combat' : '\n✗ Cannot use in combat'}`;
        
        return `
            <div class="item-entry" data-tooltip="${tooltipText}" title="${item.description || item.name}">
                <span class="item-icon">${rarityEmoji[item.rarity] || '⚪'}</span>
                <span class="item-name">${item.name}</span>
            </div>
        `;
    }).join('');
}

// Show item selection modal
function showItemModal() {
    if (!gameState.player || !gameState.player.inventory || gameState.player.inventory.length === 0) {
        addLogEntry('No items to use!', 'danger');
        return;
    }
    
    elements.itemModal.classList.add('active');
    
    const itemList = elements.modalItemList;
    itemList.innerHTML = gameState.player.inventory.map(item => {
        const rarityEmoji = {
            'common': '⚪',
            'uncommon': '🟢',
            'rare': '🔵',
            'epic': '🟣',
            'legendary': '🟡'
        };
        
        return `
            <div class="item-card" data-item-id="${item.item_id}">
                <div class="item-header">
                    <span class="item-icon">${rarityEmoji[item.rarity] || '⚪'}</span>
                    <span class="item-title">${item.name}</span>
                </div>
                <div class="item-description">${item.description || 'A useful item'}</div>
                <div class="item-stats">
                    <span class="item-type">${item.effect_type || 'unknown'}</span>
                    <span class="item-value">Effect: ${item.effect_value || 0}</span>
                </div>
                <button class="btn btn-primary btn-use-item" data-item-id="${item.item_id}">Use Item</button>
            </div>
        `;
    }).join('');
    
    // Attach click handlers to use buttons
    itemList.querySelectorAll('.btn-use-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const itemId = e.target.getAttribute('data-item-id');
            useItem(itemId);
        });
    });
}

// Use an item
async function useItem(itemId) {
    elements.itemModal.classList.remove('active');
    
    addLogEntry('Using item...', 'info');
    
    const result = await apiRequest('/inventory/use', 'POST', {
        session_id: gameState.sessionId,
        item_id: itemId
    });
    
    if (result.error) {
        addLogEntry(`Failed to use item: ${result.message}`, 'danger');
        return;
    }
    
    // Update player stats from response
    if (result.data) {
        const useResult = result.data.use_result || {};
        addLogEntry(useResult.message || result.message || 'Item used successfully!', 'success');
        
        // Update player stats from player_stats in response
        if (result.data.player_stats) {
            gameState.player.health = result.data.player_stats.health;
            gameState.player.attack_power = result.data.player_stats.attack_power;
            gameState.player.defense = result.data.player_stats.defense;
            gameState.player.gold = result.data.player_stats.gold;
        }
        
        // Remove item from local inventory
        if (gameState.player.inventory) {
            gameState.player.inventory = gameState.player.inventory.filter(item => item.item_id !== itemId);
        }
        
        updatePlayerDisplay();
        updateInventoryDisplay();
        
        // If enemy was affected, update enemy display
        if (result.data.enemy_stats && gameState.currentEnemy) {
            gameState.currentEnemy.health = result.data.enemy_stats.health.split('/')[0];
            gameState.currentEnemy.max_health = result.data.enemy_stats.health.split('/')[1];
            showCombatArea();
        }
    }
}

// Update room display
function updateRoomDisplay() {
    if (!gameState.currentRoom) return;
    
    elements.roomName.textContent = gameState.currentRoom.name || 'Unknown Room';
    elements.roomDescription.textContent = gameState.currentRoom.description || 'A mysterious room...';
    
    // Update room features
    elements.roomFeatures.innerHTML = '';
    
    if (gameState.currentRoom.has_staircase) {
        const badge = document.createElement('span');
        badge.className = 'feature-badge';
        badge.textContent = '🔼 Staircase Available';
        elements.roomFeatures.appendChild(badge);
    }
    
    if (gameState.currentRoom.has_been_visited) {
        const badge = document.createElement('span');
        badge.className = 'feature-badge';
        badge.textContent = '👁️ Previously Visited';
        elements.roomFeatures.appendChild(badge);
    }
    
    // Update movement buttons
    updateMovementButtons();
}

// Update movement buttons
function updateMovementButtons() {
    const directions = ['north', 'south', 'east', 'west'];
    
    directions.forEach(dir => {
        const btn = elements[`move${dir.charAt(0).toUpperCase() + dir.slice(1)}`];
        const available = gameState.currentRoom?.available_directions?.includes(dir);
        btn.disabled = !available || gameState.inCombat;
    });
    
    elements.moveUp.disabled = !gameState.currentRoom?.has_staircase || gameState.inCombat;
}

// Move player
async function movePlayer(direction) {
    addLogEntry(`Moving ${direction}...`);
    
    const result = await apiRequest('/player/move', 'POST', {
        session_id: gameState.sessionId,
        direction: direction
    });
    
    if (result.error) {
        addLogEntry(`Cannot move: ${result.message}`, 'danger');
        return;
    }
    
    // Update game state - the API returns room_info, not new_room
    if (result.data.room_info) {
        gameState.currentRoom = result.data.room_info;
        gameState.player.room_id = result.data.moved_to || result.data.room_info.room_id;
    }
    
    // Update player stats from response
    if (result.data.player_stats) {
        gameState.player.floor = result.data.player_stats.floor;
        gameState.player.health = result.data.player_stats.health;
        gameState.player.gold = result.data.player_stats.gold;
    }
    
    // Add exploration gold if earned
    if (result.data.exploration_gold) {
        gameState.player.gold = (gameState.player.gold || 0) + result.data.exploration_gold;
    }
    
    updatePlayerDisplay();
    updateRoomDisplay();
    
    addLogEntry(result.message, 'success');
    
    if (result.data.exploration_gold > 0) {
        addLogEntry(`💰 Found ${result.data.exploration_gold} gold!`, 'success');
    }
    
    // Handle item find
    if (result.data.item_found && result.data.item_result) {
        const itemData = result.data.item_result;
        addLogEntry(`🎒 ${itemData.message}`, 'success');
        
        // Add item to player's inventory in gameState
        if (!gameState.player.inventory) {
            gameState.player.inventory = [];
        }
        gameState.player.inventory.push(itemData.item);
        updateInventoryDisplay();
    }
    
    // Handle ally encounter
    if (result.data.ally_encountered && result.data.ally_result) {
        const ally = result.data.ally_result;
        addLogEntry(`🤝 ${ally.message}`, 'success');
        gameState.player.allies_count = (gameState.player.allies_count || 0) + 1;
        updatePlayerDisplay();
    }
    
    // Handle enemy encounter
    if (result.data.encounter_occurred && result.data.encounter_result) {
        handleEncounter(result.data.encounter_result);
    }
}

// Handle encounter
function handleEncounter(encounterData) {
    if (!encounterData || !encounterData.data) return;
    
    const encounter = encounterData.data;
    gameState.inCombat = true;
    gameState.currentEnemy = encounter.enemy;
    gameState.currentAlly = encounter.ally || null;
    
    // Update player state from encounter
    if (encounter.player) {
        gameState.player.in_battle = true;
        gameState.player.health = encounter.player.health;
    }
    
    addLogEntry(`⚔️ ${encounterData.message}`, 'danger');
    if (encounter.description) {
        addLogEntry(encounter.description);
    }
    if (encounter.enemy && encounter.enemy.description) {
        addLogEntry(encounter.enemy.description);
    }
    
    showCombatArea();
    updatePlayerDisplay();
    updateMovementButtons();
}

// Show combat area
function showCombatArea() {
    elements.combatArea.classList.remove('hidden');
    
    if (gameState.currentEnemy) {
        elements.enemyName.textContent = gameState.currentEnemy.name || 'Unknown Enemy';
        elements.enemyDescription.textContent = gameState.currentEnemy.description || 'A mysterious creature';
        
        const currentHealth = gameState.currentEnemy.health || 0;
        const maxHealth = gameState.currentEnemy.max_health || 1;
        const enemyHealthPercent = (currentHealth / maxHealth) * 100;
        
        elements.enemyHealthBar.style.width = `${enemyHealthPercent}%`;
        elements.enemyHealthText.textContent = `${currentHealth}/${maxHealth}`;
        
        elements.enemyAttack.textContent = gameState.currentEnemy.attack_power || 0;
        elements.enemyDefense.textContent = gameState.currentEnemy.defense || 0;
    }
    
    // Show/hide ally button
    if (gameState.currentAlly && !gameState.currentAlly.used) {
        elements.useAllyBtn.classList.remove('hidden');
    } else {
        elements.useAllyBtn.classList.add('hidden');
    }
    
    // Show/hide item button based on inventory
    if (gameState.player && gameState.player.inventory && gameState.player.inventory.length > 0) {
        elements.useItemBtn.classList.remove('hidden');
    } else {
        elements.useItemBtn.classList.add('hidden');
    }
}

// Hide combat area
function hideCombatArea() {
    elements.combatArea.classList.add('hidden');
    gameState.inCombat = false;
    gameState.currentEnemy = null;
    gameState.currentAlly = null;
    updateMovementButtons();
}

// Perform combat action
async function performCombatAction(action, useAlly = false) {
    const result = await apiRequest('/player/attack', 'POST', {
        session_id: gameState.sessionId,
        action: action,
        use_ally: useAlly
    });
    
    if (result.error) {
        addLogEntry(`Combat error: ${result.message}`, 'danger');
        return;
    }
    
    // Process combat result
    if (result.data) {
        const combatData = result.data;
        
        // Add combat messages to log
        if (combatData.messages) {
            combatData.messages.forEach(msg => {
                // Check if message is an object with a description field
                const messageText = typeof msg === 'object' && msg.description ? msg.description : msg;
                addLogEntry(messageText, 'important');
            });
        }
        
        // Update player state
        if (combatData.player) {
            gameState.player.health = combatData.player.health;
            gameState.player.gold = combatData.player.gold;
            gameState.player.level = combatData.player.level;
            gameState.player.in_battle = combatData.player.in_battle;
            updatePlayerDisplay();
        }
        
        // Update enemy state
        if (combatData.enemy && gameState.inCombat) {
            gameState.currentEnemy = combatData.enemy;
            showCombatArea();
        }
        
        // Check if battle ended
        if (combatData.battle_ended || !combatData.player?.in_battle) {
            if (combatData.victory) {
                addLogEntry(`🎉 Victory! Gained ${combatData.gold_reward} gold and ${combatData.exp_reward} XP!`, 'success');
            } else if (combatData.fled) {
                addLogEntry(`🏃 Successfully fled from battle!`, 'success');
            }
            hideCombatArea();
        }
        
        // Check if player died
        if (combatData.player && !combatData.player.is_alive) {
            handlePlayerDeath();
        }
    }
}

// Handle player death
function handlePlayerDeath() {
    addLogEntry('💀 You have fallen in battle...', 'danger');
    
    setTimeout(() => {
        elements.finalGold.textContent = gameState.player.gold;
        elements.finalLevel.textContent = gameState.player.level || 1;
        elements.finalFloor.textContent = gameState.player.floor;
        elements.finalAllies.textContent = gameState.player.allies_count || 0;
        
        showScreen('game-over-screen');
    }, 2000);
}

// View stats
async function viewStats() {
    elements.statsModal.classList.add('active');
    elements.modalStatsContent.innerHTML = '<p class="loading">Loading statistics...</p>';
    
    const result = await apiRequest('/player/stats', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        elements.modalStatsContent.innerHTML = `<p class="danger">Error loading stats: ${result.message}</p>`;
        return;
    }
    
    if (result.data) {
        const stats = result.data;
        elements.modalStatsContent.innerHTML = `
            <div class="stat-category">
                <h3>Character Stats</h3>
                <div class="stat-row">
                    <span class="stat-label">Name:</span>
                    <span class="stat-value">${stats.name || 'Unknown'}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Level:</span>
                    <span class="stat-value">${stats.level || 1}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Experience:</span>
                    <span class="stat-value">${stats.experience || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Health:</span>
                    <span class="stat-value">${stats.health || '0/0'}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Attack Power:</span>
                    <span class="stat-value">${stats.attack_power || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Defense:</span>
                    <span class="stat-value">${stats.defense || 0}</span>
                </div>
            </div>
            <div class="stat-category">
                <h3>Progress</h3>
                <div class="stat-row">
                    <span class="stat-label">Current Floor:</span>
                    <span class="stat-value">${stats.floor || 1}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Gold:</span>
                    <span class="stat-value">${stats.gold || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Allies:</span>
                    <span class="stat-value">${stats.allies_count || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Score:</span>
                    <span class="stat-value">${stats.score || stats.gold || 0}</span>
                </div>
            </div>
        `;
    }
}

// Load leaderboard
async function loadLeaderboard() {
    const result = await apiRequest('/scores/highscores?limit=10', 'GET');
    
    if (result.error) {
        elements.leaderboardList.innerHTML = '<p class="empty-state">Failed to load leaderboard</p>';
        return;
    }
    
    displayLeaderboard(result.data || [], elements.leaderboardList);
}

// Show leaderboard modal
async function showLeaderboardModal() {
    elements.leaderboardModal.classList.add('active');
    elements.modalLeaderboardList.innerHTML = '<p class="loading">Loading leaderboard...</p>';
    
    const result = await apiRequest('/scores/highscores?limit=20', 'GET');
    
    if (result.error) {
        elements.modalLeaderboardList.innerHTML = '<p class="empty-state">Failed to load leaderboard</p>';
        return;
    }
    
    displayLeaderboard(result.data || [], elements.modalLeaderboardList);
}

// Display leaderboard
function displayLeaderboard(scores, container) {
    if (!scores || scores.length === 0) {
        container.innerHTML = '<p class="empty-state">No scores yet. Be the first!</p>';
        return;
    }
    
    container.innerHTML = scores.map((entry, index) => {
        const rank = index + 1;
        const rankClass = rank <= 3 ? `rank-${rank}` : '';
        
        return `
            <div class="leaderboard-entry ${rankClass}">
                <div class="leaderboard-rank">#${rank}</div>
                <div class="leaderboard-info">
                    <div class="leaderboard-name">${entry.player_name || 'Anonymous'}</div>
                    <div class="leaderboard-details">Floor ${entry.floor || 1} • Level ${entry.level || 1}</div>
                </div>
                <div class="leaderboard-score">${entry.score || entry.gold || 0} 💰</div>
            </div>
        `;
    }).join('');
}

// Submit score
async function submitScore() {
    if (!gameState.sessionId) {
        addLogEntry('No active game session', 'danger');
        return;
    }
    
    const result = await apiRequest('/scores/submit', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        addLogEntry(`Failed to submit score: ${result.message}`, 'danger');
        return;
    }
    
    addLogEntry('Score submitted successfully!', 'success');
    loadLeaderboard();
}

// Confirm new game
function confirmNewGame() {
    if (confirm('Are you sure you want to start a new game? Your current progress will be lost.')) {
        showScreen('start-screen');
        resetGameState();
    }
}

// Reset game state
function resetGameState() {
    gameState.sessionId = null;
    gameState.player = null;
    gameState.currentRoom = null;
    gameState.inCombat = false;
    gameState.currentEnemy = null;
    gameState.currentAlly = null;
    
    elements.eventLog.innerHTML = '<p class="log-entry">Your adventure begins...</p>';
    elements.playerNameInput.value = '';
    
    hideCombatArea();
}

// Show screen
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    document.getElementById(screenId).classList.add('active');
}

// Add log entry
function addLogEntry(message, type = '') {
    const entry = document.createElement('p');
    entry.className = `log-entry ${type}`;
    entry.textContent = message;
    
    elements.eventLog.appendChild(entry);
    elements.eventLog.scrollTop = elements.eventLog.scrollHeight;
    
    // Limit log entries to prevent memory issues
    const entries = elements.eventLog.children;
    if (entries.length > 50) {
        entries[0].remove();
    }
}

// Utility: Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
