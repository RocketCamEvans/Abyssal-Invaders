// Abyssal Invaders - Game Logic

// Game State
const gameState = {
    sessionId: null,
    player: null,
    currentRoom: null,
    inCombat: false,
    currentEnemy: null,
    currentAlly: null,
    roomPositions: {}, // Track room positions for minimap: { roomId: {x, y} }
    roomInfo: {} // Track room features for minimap: { roomId: {hasStairs: bool} }
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
        enterShopBtn: document.getElementById('enter-shop'),
        enterCasinoBtn: document.getElementById('enter-casino'),
        
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
        allyModal: document.getElementById('ally-modal'),
        shopModal: document.getElementById('shop-modal'),
        modalLeaderboardList: document.getElementById('modal-leaderboard-list'),
        modalStatsContent: document.getElementById('modal-stats-content'),
        modalItemList: document.getElementById('modal-item-list'),
        modalAllyList: document.getElementById('modal-ally-list'),
        modalShopList: document.getElementById('modal-shop-list'),
        shopPlayerGold: document.getElementById('shop-player-gold'),
        
        // Casino elements
        casinoModal: document.getElementById('casino-modal'),
        casinoPlayerGold: document.getElementById('casino-player-gold'),
        casinoBetScreen: document.getElementById('casino-bet-screen'),
        casinoGameScreen: document.getElementById('casino-game-screen'),
        betAmount: document.getElementById('bet-amount'),
        startBlackjackBtn: document.getElementById('start-blackjack-btn'),
        dealerCards: document.getElementById('dealer-cards'),
        playerCards: document.getElementById('player-cards'),
        dealerValue: document.getElementById('dealer-value'),
        playerValue: document.getElementById('player-value'),
        hitBtn: document.getElementById('hit-btn'),
        standBtn: document.getElementById('stand-btn'),
        gameMessage: document.getElementById('game-message'),
        newHandBtn: document.getElementById('new-hand-btn'),
        
        // Minimap
        minimapFloor: document.getElementById('minimap-floor'),
        minimapGrid: document.getElementById('minimap-grid')
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
    elements.enterShopBtn.addEventListener('click', openShop);
    elements.enterCasinoBtn.addEventListener('click', openCasino);
    
    // Combat
    elements.attackBtn.addEventListener('click', () => performCombatAction('attack', false));
    elements.useAllyBtn.addEventListener('click', () => showAllyModal());
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
    
    // Casino event listeners
    elements.startBlackjackBtn.addEventListener('click', startBlackjack);
    elements.hitBtn.addEventListener('click', blackjackHit);
    elements.standBtn.addEventListener('click', blackjackStand);
    elements.newHandBtn.addEventListener('click', () => {
        elements.casinoBetScreen.classList.remove('hidden');
        elements.casinoGameScreen.classList.add('hidden');
        elements.betAmount.value = '';
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
    if (!gameState.player.allies) gameState.player.allies = [];
    if (!gameState.player.allies_count) gameState.player.allies_count = 0;
    if (!gameState.player.level) gameState.player.level = 1;
    if (!gameState.player.attack_power) gameState.player.attack_power = 10;
    if (!gameState.player.defense) gameState.player.defense = 5;
    if (!gameState.player.inventory) gameState.player.inventory = [];
    
    // Load inventory from API if provided
    if (result.data.player.inventory) {
        gameState.player.inventory = result.data.player.inventory;
    }
    
    // Load allies from API if provided
    if (result.data.player.allies) {
        gameState.player.allies = result.data.player.allies;
    }
    
    // Initialize room positions for minimap (start at 0,0)
    gameState.roomPositions = {};
    gameState.roomPositions[gameState.player.room_id] = { x: 0, y: 0 };
    
    // Initialize room info for minimap
    gameState.roomInfo = {};
    gameState.roomInfo[gameState.player.room_id] = {
        hasStairs: gameState.currentRoom.has_staircase || false,
        isShop: gameState.currentRoom.is_shop || false,
        isCasino: gameState.currentRoom.is_casino || false
    };
    
    showScreen('game-screen');
    updatePlayerDisplay();
    updateRoomDisplay();
    updateMinimap(); // Initialize minimap on game start
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
    elements.playerAllies.textContent = gameState.player.allies ? gameState.player.allies.length : 0;
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
    
    if (!gameState.player || !gameState.player.allies || gameState.player.allies.length === 0) {
        alliesList.innerHTML = '<p class="empty-state">No allies recruited yet</p>';
        return;
    }
    
    // Display actual ally details
    alliesList.innerHTML = gameState.player.allies.map((ally, index) => {
        const typeEmoji = {
            'healer': '💚',
            'attacker': '⚔️',
            'skipper': '⏸️'
        };
        
        return `
            <div class="ally-card" data-ally-index="${index}">
                <div class="ally-header">
                    <span class="ally-icon">${typeEmoji[ally.type] || '🤝'}</span>
                    <span class="ally-name">${ally.name}</span>
                </div>
                <div class="ally-type">${ally.type} - ${ally.value > 0 ? ally.value : 'Skip Turn'}</div>
            </div>
        `;
    }).join('');
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

// Show ally selection modal
function showAllyModal() {
    if (!gameState.player || !gameState.player.allies || gameState.player.allies.length === 0) {
        addLogEntry('No allies available!', 'danger');
        return;
    }
    
    if (gameState.player.ally_used) {
        addLogEntry('You can only use one ally per battle!', 'danger');
        return;
    }
    
    elements.allyModal.classList.add('active');
    
    const allyList = elements.modalAllyList;
    allyList.innerHTML = gameState.player.allies.map((ally, index) => {
        const typeEmoji = {
            'healer': '💚',
            'attacker': '⚔️',
            'skipper': '⏸️'
        };
        
        const typeDescription = {
            'healer': `Heals ${ally.value} HP`,
            'attacker': `Deals ${ally.value} damage`,
            'skipper': 'Skips enemy turn'
        };
        
        return `
            <div class="ally-card" data-ally-index="${index}">
                <div class="ally-header">
                    <span class="ally-icon">${typeEmoji[ally.type] || '👤'}</span>
                    <span class="ally-title">${ally.name}</span>
                </div>
                <div class="ally-description">${ally.description || typeDescription[ally.type]}</div>
                <div class="ally-stats">
                    <span class="ally-type">${ally.type}</span>
                    <span class="ally-value">${typeDescription[ally.type]}</span>
                </div>
                <button class="btn btn-primary btn-use-ally" data-ally-index="${index}">Call Ally</button>
            </div>
        `;
    }).join('');
    
    // Attach click handlers to use buttons
    allyList.querySelectorAll('.btn-use-ally').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const allyIndex = parseInt(e.target.getAttribute('data-ally-index'));
            useAlly(allyIndex);
        });
    });
}

// Use an ally
async function useAlly(allyIndex) {
    elements.allyModal.classList.remove('active');
    
    addLogEntry('Calling ally...', 'info');
    
    await performCombatAction('attack', false, allyIndex);
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
    
    // Show/hide shop button
    if (gameState.currentRoom.is_shop) {
        elements.enterShopBtn.classList.remove('hidden');
        const badge = document.createElement('span');
        badge.className = 'feature-badge';
        badge.style.background = 'linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)';
        badge.textContent = '🏪 Shop Available';
        elements.roomFeatures.appendChild(badge);
    } else {
        elements.enterShopBtn.classList.add('hidden');
    }
    
    // Show/hide casino button
    if (gameState.currentRoom.is_casino) {
        elements.enterCasinoBtn.classList.remove('hidden');
        const badge = document.createElement('span');
        badge.className = 'feature-badge';
        badge.style.background = 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)';
        badge.textContent = '🎰 Casino Available';
        elements.roomFeatures.appendChild(badge);
    } else {
        elements.enterCasinoBtn.classList.add('hidden');
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
    
    // Track old room ID before updating
    const oldRoomId = gameState.player.room_id;
    
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
        gameState.player.room_id = result.data.player_stats.room_id;
        if (result.data.player_stats.visited_rooms) {
            gameState.player.visited_rooms = result.data.player_stats.visited_rooms;
        }
    }
    
    // Ensure current room is in visited_rooms (API may lag behind)
    if (!gameState.player.visited_rooms) {
        gameState.player.visited_rooms = [];
    }
    if (!gameState.player.visited_rooms.includes(gameState.player.room_id)) {
        gameState.player.visited_rooms.push(gameState.player.room_id);
    }
    
    // Update room position for minimap based on movement direction
    updateRoomPosition(oldRoomId, gameState.player.room_id, result.data.direction);
    
    // Store room info for minimap AFTER position update (in case of floor reset)
    if (result.data.room_info) {
        gameState.roomInfo[gameState.player.room_id] = {
            hasStairs: result.data.room_info.has_staircase || false,
            isShop: result.data.room_info.is_shop || false,
            isCasino: result.data.room_info.is_casino || false
        };
    }
    
    // Add exploration gold if earned
    if (result.data.exploration_gold) {
        gameState.player.gold = (gameState.player.gold || 0) + result.data.exploration_gold;
    }
    
    updatePlayerDisplay();
    updateRoomDisplay();
    updateMinimap(); // Update minimap after room data is loaded
    
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
        
        // Initialize allies array if needed
        if (!gameState.player.allies) {
            gameState.player.allies = [];
        }
        
        // Add the ally to the player's allies array
        if (ally.ally) {
            gameState.player.allies.push(ally.ally);
        }
        
        updatePlayerDisplay();
        updateAlliesList();
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
        // Reset ally_used flag for new battle
        gameState.player.ally_used = false;
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
    
    // Show/hide ally button based on allies array AND if ally hasn't been used this battle
    if (gameState.player && gameState.player.allies && gameState.player.allies.length > 0 && !gameState.player.ally_used) {
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
async function performCombatAction(action, useAlly = false, allyIndex = null) {
    const requestBody = {
        session_id: gameState.sessionId,
        action: action,
        use_ally: useAlly
    };
    
    // Add ally_index if provided
    if (allyIndex !== null) {
        requestBody.ally_index = allyIndex;
        requestBody.use_ally = true;
    }
    
    const result = await apiRequest('/player/attack', 'POST', requestBody);
    
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
            gameState.player.allies = combatData.player.allies || [];
            gameState.player.ally_used = combatData.player.ally_used || false;
            updatePlayerDisplay();
            updateAlliesList();
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

// Update room position based on movement direction
function updateRoomPosition(fromRoomId, toRoomId, direction) {
    console.log(`Minimap: updateRoomPosition from ${fromRoomId} to ${toRoomId} via ${direction}`);
    
    // Handle floor change FIRST - reset everything before any position calculations
    if (direction === 'up') {
        console.log(`Minimap: Floor change detected, resetting all positions`);
        gameState.roomPositions = {};
        gameState.roomInfo = {};
        // Set the new floor's start room to (0, 0)
        gameState.roomPositions[toRoomId] = { x: 0, y: 0 };
        console.log(`Minimap: Set ${toRoomId} to position (0, 0) on new floor`);
        return; // Exit early, we're done
    }
    
    // If we don't know the old room position, initialize it
    if (!gameState.roomPositions[fromRoomId]) {
        gameState.roomPositions[fromRoomId] = { x: 0, y: 0 };
        console.log(`Minimap: Initialized ${fromRoomId} at (0, 0)`);
    }
    
    // If we already know the new room position, don't update (backtracking)
    if (gameState.roomPositions[toRoomId]) {
        console.log(`Minimap: ${toRoomId} already has position, skipping update`);
        return;
    }
    
    // Calculate new position based on direction
    const oldPos = gameState.roomPositions[fromRoomId];
    const newPos = { ...oldPos };
    
    switch (direction) {
        case 'north':
            newPos.y -= 1;
            break;
        case 'south':
            newPos.y += 1;
            break;
        case 'east':
            newPos.x += 1;
            break;
        case 'west':
            newPos.x -= 1;
            break;
    }
    
    console.log(`Minimap: Calculated position for ${toRoomId}: (${newPos.x}, ${newPos.y})`);
    
    // Check if another room is already at this position (position conflict)
    const existingRoomAtPos = Object.entries(gameState.roomPositions).find(
        ([roomId, pos]) => roomId !== toRoomId && pos.x === newPos.x && pos.y === newPos.y
    );
    
    if (existingRoomAtPos) {
        // Position conflict! Offset the new room slightly to avoid overlap
        console.log(`Minimap: Position conflict at (${newPos.x}, ${newPos.y}) with room ${existingRoomAtPos[0]}. Offsetting new room.`);
        // Try to find an adjacent free position
        const offsets = [[0, 1], [1, 0], [0, -1], [-1, 0], [1, 1], [-1, -1], [1, -1], [-1, 1]];
        let foundFree = false;
        for (const [dx, dy] of offsets) {
            const testPos = { x: newPos.x + dx, y: newPos.y + dy };
            const conflict = Object.entries(gameState.roomPositions).find(
                ([roomId, pos]) => pos.x === testPos.x && pos.y === testPos.y
            );
            if (!conflict) {
                console.log(`Minimap: Found free position at (${testPos.x}, ${testPos.y})`);
                newPos.x = testPos.x;
                newPos.y = testPos.y;
                foundFree = true;
                break;
            }
        }
        if (!foundFree) {
            console.warn(`Minimap: Could not find free position near (${newPos.x}, ${newPos.y}), using anyway`);
        }
    }
    
    gameState.roomPositions[toRoomId] = newPos;
    console.log(`Minimap: Set ${toRoomId} to position (${newPos.x}, ${newPos.y})`);
}

// Minimap functions
function updateMinimap() {
    if (!gameState.player) {
        console.log('Minimap: No player data');
        return;
    }
    
    // Update floor display
    elements.minimapFloor.textContent = gameState.player.floor || 1;
    
    // Get visited rooms
    let visitedRooms = [];
    if (Array.isArray(gameState.player.visited_rooms)) {
        visitedRooms = gameState.player.visited_rooms;
    } else if (gameState.player.visited_rooms) {
        visitedRooms = Array.from(gameState.player.visited_rooms);
    }
    
    if (visitedRooms.length === 0) {
        elements.minimapGrid.innerHTML = '<p class="empty-state">Explore to reveal map</p>';
        return;
    }
    
    const currentRoom = gameState.player.room_id;
    
    // Build room coords from position tracking
    const roomCoords = visitedRooms.map(roomId => {
        const pos = gameState.roomPositions[roomId];
        if (!pos) return null;
        
        const roomData = gameState.roomInfo[roomId] || {};
        
        return {
            roomId: roomId,
            x: pos.x,
            y: pos.y,
            isCurrent: roomId === currentRoom,
            hasStairs: roomData.hasStairs || false,
            isShop: roomData.isShop || false,
            isCasino: roomData.isCasino || false
        };
    }).filter(coord => coord !== null);
    
    if (roomCoords.length === 0) {
        elements.minimapGrid.innerHTML = '<p class="empty-state">Explore to reveal map</p>';
        return;
    }
    
    // Find bounds
    const minX = Math.min(...roomCoords.map(c => c.x));
    const maxX = Math.max(...roomCoords.map(c => c.x));
    const minY = Math.min(...roomCoords.map(c => c.y));
    const maxY = Math.max(...roomCoords.map(c => c.y));
    
    // Center the map view around current position
    const currentCoord = roomCoords.find(c => c.isCurrent);
    let centerX = currentCoord ? currentCoord.x : (minX + maxX) / 2;
    let centerY = currentCoord ? currentCoord.y : (minY + maxY) / 2;
    
    // 7x7 grid centered on player
    const gridSize = 7;
    const halfSize = Math.floor(gridSize / 2);
    
    const startX = Math.floor(centerX - halfSize);
    const startY = Math.floor(centerY - halfSize);
    
    // Create grid
    elements.minimapGrid.innerHTML = '';
    elements.minimapGrid.style.display = 'grid';
    
    for (let y = startY; y < startY + gridSize; y++) {
        for (let x = startX; x < startX + gridSize; x++) {
            const cell = document.createElement('div');
            cell.className = 'minimap-cell';
            
            // Find if this coordinate is visited
            const room = roomCoords.find(c => c.x === x && c.y === y);
            
            if (room) {
                if (room.isCurrent) {
                    cell.classList.add('current');
                    cell.textContent = '●';
                    cell.title = 'Current Location';
                } else if (room.isShop) {
                    cell.classList.add('shop');
                    cell.textContent = '🏪';
                    cell.title = 'Shop';
                } else if (room.isCasino) {
                    cell.classList.add('casino');
                    cell.textContent = '🎰';
                    cell.title = 'Casino';
                } else if (room.hasStairs) {
                    cell.classList.add('stairs');
                    cell.textContent = '▲';
                    cell.title = 'Stairs';
                } else {
                    cell.classList.add('visited');
                    cell.textContent = '○';
                    cell.title = 'Visited';
                }
            } else {
                cell.classList.add('empty');
                cell.textContent = '';
            }
            
            elements.minimapGrid.appendChild(cell);
        }
    }
}

// Shop functions
async function openShop() {
    addLogEntry('Entering the shop...', 'info');
    
    const result = await apiRequest('/shop/view', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        addLogEntry(`Shop error: ${result.message}`, 'danger');
        return;
    }
    
    // Update player gold display in shop
    elements.shopPlayerGold.textContent = result.data.player_gold;
    
    // Display shop items
    displayShopItems(result.data.shop_items);
    
    // Show shop modal
    elements.shopModal.classList.add('active');
}

function displayShopItems(items) {
    elements.modalShopList.innerHTML = '';
    
    if (!items || items.length === 0) {
        elements.modalShopList.innerHTML = '<p class="empty-state">Shop is sold out!</p>';
        return;
    }
    
    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'shop-item';
        
        itemDiv.innerHTML = `
            <div class="shop-item-info">
                <div class="shop-item-name">${item.name}</div>
                <div class="shop-item-description">${item.description}</div>
                <span class="shop-item-rarity ${item.rarity}">${item.rarity}</span>
            </div>
            <div class="shop-item-purchase">
                <div class="shop-item-price">💰 ${item.price}g</div>
                <button class="shop-buy-btn" onclick="purchaseShopItem('${item.name}', ${item.price})">
                    Buy
                </button>
            </div>
        `;
        
        elements.modalShopList.appendChild(itemDiv);
    });
}

async function purchaseShopItem(itemName, price) {
    // Check if player has enough gold
    if (gameState.player.gold < price) {
        addLogEntry(`Not enough gold! Need ${price}, have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    addLogEntry(`Purchasing ${itemName}...`, 'info');
    
    const result = await apiRequest('/shop/purchase', 'POST', {
        session_id: gameState.sessionId,
        item_name: itemName
    });
    
    if (result.error) {
        addLogEntry(`Purchase failed: ${result.message}`, 'danger');
        return;
    }
    
    // Update player gold
    gameState.player.gold = result.data.gold_remaining;
    gameState.player.inventory = result.data.inventory;
    
    updatePlayerDisplay();
    updateInventoryDisplay();
    
    addLogEntry(result.message, 'success');
    
    // Refresh shop display
    openShop();
}

// Casino functions
async function openCasino() {
    addLogEntry('Entering the casino...', 'info');
    
    const result = await apiRequest('/casino/enter', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        addLogEntry(`Casino error: ${result.message}`, 'danger');
        return;
    }
    
    // Update player gold display in casino
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    
    // Reset casino screens
    elements.casinoBetScreen.classList.remove('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    elements.betAmount.value = '';
    
    // Show casino modal
    elements.casinoModal.classList.add('active');
}

// Start a new blackjack game
async function startBlackjack() {
    const bet = parseInt(elements.betAmount.value);
    
    if (!bet || bet <= 0) {
        addLogEntry('Please enter a valid bet amount', 'danger');
        return;
    }
    
    if (bet > gameState.player.gold) {
        addLogEntry(`Not enough gold! You have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    addLogEntry(`Starting blackjack with ${bet} gold bet...`, 'info');
    
    const result = await apiRequest('/casino/blackjack/start', 'POST', {
        session_id: gameState.sessionId,
        bet: bet
    });
    
    if (result.error) {
        addLogEntry(`Error: ${result.message}`, 'danger');
        return;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = gameState.player.gold;
    updatePlayerDisplay();
    
    // Display game
    displayBlackjackGame(result.data.game);
    
    // Show game screen
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.remove('hidden');
    
    addLogEntry(result.message, 'success');
}

// Hit in blackjack
async function blackjackHit() {
    const result = await apiRequest('/casino/blackjack/hit', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        addLogEntry(`Error: ${result.message}`, 'danger');
        return;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = gameState.player.gold;
    updatePlayerDisplay();
    
    // Display game
    displayBlackjackGame(result.data.game);
    
    if (result.data.game.message) {
        addLogEntry(result.data.game.message, result.data.game.game_over ? 'important' : 'info');
    }
}

// Stand in blackjack
async function blackjackStand() {
    const result = await apiRequest('/casino/blackjack/stand', 'POST', {
        session_id: gameState.sessionId
    });
    
    if (result.error) {
        addLogEntry(`Error: ${result.message}`, 'danger');
        return;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = gameState.player.gold;
    updatePlayerDisplay();
    
    // Display game
    displayBlackjackGame(result.data.game);
    
    if (result.data.game.message) {
        addLogEntry(result.data.game.message, 'important');
    }
}

// Display blackjack game state
function displayBlackjackGame(game) {
    // Display dealer cards
    elements.dealerCards.innerHTML = game.dealer_cards.map(card => 
        `<span class="playing-card">${card}</span>`
    ).join(' ');
    elements.dealerValue.textContent = game.dealer_value;
    
    // Display player cards
    elements.playerCards.innerHTML = game.player_cards.map(card => 
        `<span class="playing-card">${card}</span>`
    ).join(' ');
    elements.playerValue.textContent = game.player_value;
    
    // Show/hide controls based on game state
    if (game.game_over) {
        elements.hitBtn.classList.add('hidden');
        elements.standBtn.classList.add('hidden');
        elements.newHandBtn.classList.remove('hidden');
        
        // Display result message
        elements.gameMessage.textContent = game.message || '';
        elements.gameMessage.className = 'game-message ' + 
            (game.result === 'win' || game.result === 'blackjack' ? 'success' : 
             game.result === 'loss' || game.result === 'bust' ? 'danger' : 'info');
    } else {
        elements.hitBtn.classList.remove('hidden');
        elements.standBtn.classList.remove('hidden');
        elements.newHandBtn.classList.add('hidden');
        elements.gameMessage.textContent = '';
    }
}
