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
    roomInfo: {}, // Track room features for minimap: { roomId: {hasStairs: bool} }
    isLoading: false, // Track if a request is in progress
    loadingMessage: '', // Store the current loading message
    enemySprite: null, // Cache the current enemy's sprite
    spriteCache: {}, // Cache sprites by enemy name: { enemyName: spritePath }
    playerSprite: null, // Cache the player's sprite
    timingBarActive: false, // Track if timing bar mini-game is active
    timingBarPosition: 0, // Current position of timing indicator (0-100)
    timingBarDirection: 1, // Direction of movement (1 or -1)
    timingBarSpeed: 2, // Speed of movement (pixels per frame)
    timingBarInterval: null // Interval ID for animation
};

// Make gameState globally accessible for dev tools
window.gameState = gameState;

// Element emoji mapping for office departments
function getElementEmoji(element) {
    const emojiMap = {
        'accounting': '📊',
        'it': '💻',
        'marketing': '📱',
        'hr': '👔',
        'sales': '💼',
        'legal': '⚖️',
        'management': '👨‍💼',
        'intern': '☕'
    };
    return emojiMap[element] || '❓';
}

// Format element name with proper capitalization
function formatElementName(element) {
    if (element === 'hr') {
        return 'HR';
    } else if (element === 'it') {
        return 'IT';
    } else {
        return element.charAt(0).toUpperCase() + element.slice(1);
    }
}

// Get element effectiveness multiplier (for UI hints)
function getElementAdvantage(attackerElement, defenderElement) {
    const elements = {
        'accounting': { strong: ['marketing', 'hr'], weak: ['it', 'management'] },
        'it': { strong: ['accounting', 'sales'], weak: ['hr', 'marketing'] },
        'marketing': { strong: ['it', 'legal'], weak: ['accounting', 'management'] },
        'hr': { strong: ['it', 'management'], weak: ['accounting', 'legal'] },
        'sales': { strong: ['hr', 'legal'], weak: ['it', 'accounting'] },
        'legal': { strong: ['accounting', 'sales'], weak: ['marketing', 'management'] },
        'management': { strong: ['marketing', 'sales'], weak: ['hr', 'it'] },
        'intern': { strong: [], weak: [] }
    };
    
    if (!elements[attackerElement]) return 'neutral';
    
    if (elements[attackerElement].strong.includes(defenderElement)) {
        return 'advantage';
    } else if (elements[attackerElement].weak.includes(defenderElement)) {
        return 'disadvantage';
    }
    return 'neutral';
}

// API Base URL
const API_BASE = '/api';

// DOM Elements
let elements = {};

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
    
    // Check for auto-resume from dev tools
    const autoResumeSession = localStorage.getItem('dev_auto_resume');
    if (autoResumeSession) {
        console.log('Auto-resuming session from dev tools:', autoResumeSession);
        localStorage.removeItem('dev_auto_resume'); // Clear after use
        
        // Auto-load the session
        continueGameWithSession(autoResumeSession);
    } else {
        showScreen('start-screen');
        loadLeaderboard();
    }
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
        continueSessionIdInput: document.getElementById('continue-session-id'),
        continueGameBtn: document.getElementById('continue-game-btn'),
        
        // Player info
        playerNameDisplay: document.getElementById('player-name-display'),
        playerAvatar: document.getElementById('player-avatar'),
        healthBar: document.getElementById('health-bar'),
        healthText: document.getElementById('health-text'),
        playerGold: document.getElementById('player-gold'),
        playerLevel: document.getElementById('player-level'),
        playerFloor: document.getElementById('player-floor'),
        playerAllies: document.getElementById('player-allies'),
        playerAttack: document.getElementById('player-attack'),
        playerDefense: document.getElementById('player-defense'),
        playerSpeed: document.getElementById('player-speed'),
        
        // Room display
        roomName: document.getElementById('room-name'),
        roomDescription: document.getElementById('room-description'),
        roomFeatures: document.getElementById('room-features'),
        
        // Combat
        combatArea: document.getElementById('combat-area'),
        playerSpriteContainer: document.getElementById('player-sprite-container'),
        playerSprite: document.getElementById('player-sprite'),
        enemySprite: document.getElementById('enemy-sprite'),
        enemyName: document.getElementById('enemy-name'),
        enemyDescription: document.getElementById('enemy-description'),
        enemyHealthBar: document.getElementById('enemy-health-bar'),
        enemyHealthText: document.getElementById('enemy-health-text'),
        enemyAttack: document.getElementById('enemy-attack'),
        enemyDefense: document.getElementById('enemy-defense'),
        enemySpeed: document.getElementById('enemy-speed'),
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
        showSessionBtn: document.getElementById('show-session-btn'),
        newGameBtn: document.getElementById('new-game-btn'),
        
        // Allies
        alliesList: document.getElementById('allies-list'),
        
        // Inventory
        inventoryList: document.getElementById('inventory-list'),
        
        // Leaderboard
        leaderboardList: document.getElementById('leaderboard-list'),
        
        // Game over
        deathMessage: document.getElementById('death-message'),
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
        allyDetailModal: document.getElementById('ally-detail-modal'),
        shopModal: document.getElementById('shop-modal'),
        timingBarModal: document.getElementById('timing-bar-modal'),
        timingIndicator: document.getElementById('timing-indicator'),
        timingMultiplierText: document.getElementById('timing-multiplier-text'),
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
        splitBtn: document.getElementById('split-btn'),
        
        // Gear modal elements
        gearModal: document.getElementById('gear-modal'),
        doubleBtn: document.getElementById('double-btn'),
        gameMessage: document.getElementById('game-message'),
        newHandBtn: document.getElementById('new-hand-btn'),
        // Ally detail modal elements
        allyDetailName: document.getElementById('ally-detail-name'),
        allyDetailType: document.getElementById('ally-detail-type'),
        allyDetailValue: document.getElementById('ally-detail-value'),
        allyDetailDescription: document.getElementById('ally-detail-description'),
        allyDetailSprite: document.getElementById('ally-detail-sprite'),
        
        // Ally encounter display
        allyEncounterDisplay: document.getElementById('ally-encounter-display'),
        allyEncounterName: document.getElementById('ally-encounter-name'),
        allyEncounterDescription: document.getElementById('ally-encounter-description'),
        allyEncounterSprite: document.getElementById('ally-encounter-sprite'),
        allyEncounterCloseBtn: document.getElementById('ally-encounter-close-btn'),
        
        // Ally sprite in combat
        allySpriteContainer: document.getElementById('ally-sprite-container'),
        allySprite: document.getElementById('ally-sprite'),
        
        // Minimap
        minimapFloor: document.getElementById('minimap-floor'),
        minimapGrid: document.getElementById('minimap-grid'),
        
        // Loading overlay
        loadingOverlay: document.getElementById('loading-overlay'),
        loadingMessage: document.getElementById('loading-message'),
        loadingSprite: document.getElementById('loading-sprite'),
        
        // Combat loading indicator
        combatLoadingIndicator: document.getElementById('combat-loading-indicator')
    };
}

// Attack animation classes
const ATTACK_ANIMATIONS = [
    'attack-slash',
    'attack-magic',
    'attack-lunge',
    'attack-spin',
    'attack-pulse'
];

// Player attack animations (mirrored for facing right)
const PLAYER_ATTACK_ANIMATIONS = [
    'player-attack-slash',
    'player-attack-magic',
    'player-attack-lunge',
    'player-attack-spin',
    'player-attack-pulse'
];

// Select random attack animation
function selectRandomAttackAnimation() {
    const randomIndex = Math.floor(Math.random() * ATTACK_ANIMATIONS.length);
    return ATTACK_ANIMATIONS[randomIndex];
}

// Select random player attack animation
function selectRandomPlayerAttackAnimation() {
    const randomIndex = Math.floor(Math.random() * PLAYER_ATTACK_ANIMATIONS.length);
    return PLAYER_ATTACK_ANIMATIONS[randomIndex];
}

// Remove all attack animation classes
function removeAttackAnimations() {
    if (elements.enemySprite) {
        ATTACK_ANIMATIONS.forEach(className => {
            elements.enemySprite.classList.remove(className);
        });
    }
    if (elements.playerSprite) {
        // Remove both regular and player-specific animation classes
        ATTACK_ANIMATIONS.forEach(className => {
            elements.playerSprite.classList.remove(className);
        });
        PLAYER_ATTACK_ANIMATIONS.forEach(className => {
            elements.playerSprite.classList.remove(className);
        });
    }
}

// Loading state management
function showLoading(message = 'Loading...') {
    if (gameState.isLoading) {
        console.warn('Already loading, ignoring duplicate request');
        return false;
    }
    gameState.isLoading = true;
    gameState.loadingMessage = message;
    
    if (elements.loadingMessage) {
        elements.loadingMessage.textContent = message;
    }
    
    // Apply random attack animation to enemy sprite in combat area
    if (gameState.inCombat && elements.enemySprite && elements.enemySprite.src) {
        const attackAnimation = selectRandomAttackAnimation();
        console.log(`🎬 Applying attack animation: ${attackAnimation}`);
        removeAttackAnimations(); // Clear any previous animation
        elements.enemySprite.classList.add(attackAnimation);
    }
    
    // Hide loading sprite in overlay - we want to see the combat area instead
    if (elements.loadingSprite) {
        elements.loadingSprite.classList.add('hidden');
    }
    
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.remove('hidden');
    }
    return true;
}

function hideLoading() {
    gameState.isLoading = false;
    gameState.loadingMessage = '';
    
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.add('hidden');
    }
    if (elements.loadingSprite) {
        elements.loadingSprite.classList.add('hidden');
    }
    
    // Remove attack animation from enemy sprite
    removeAttackAnimations();
}

// Fetch and cache enemy sprite
async function fetchEnemySprite(enemyName, enemyDescription) {
    console.log(`fetchEnemySprite called for: "${enemyName}"`);
    console.log(`Description: ${enemyDescription ? enemyDescription.substring(0, 100) : 'none'}...`);
    
    // Check if already cached
    if (gameState.spriteCache[enemyName]) {
        console.log(`✓ Using cached sprite for "${enemyName}": ${gameState.spriteCache[enemyName]}`);
        return gameState.spriteCache[enemyName];
    }
    
    console.log(`⟳ Fetching new sprite for "${enemyName}"...`);
    
    try {
        const result = await apiRequest('/enemy/sprite', 'POST', {
            enemy_name: enemyName,
            enemy_description: enemyDescription || ''
        });
        
        if (result.error) {
            console.error(`✗ Failed to fetch sprite for "${enemyName}":`, result.message);
            return null;
        }
        
        const spritePath = result.data.sprite_path;
        console.log(`✓ Matched sprite for "${enemyName}": ${spritePath}`);
        console.log(`  Tags: ${result.data.sprite_tags.join(', ')}`);
        
        // Cache the sprite path
        gameState.spriteCache[enemyName] = spritePath;
        gameState.enemySprite = spritePath;
        console.log(`  Cached. Total cached sprites: ${Object.keys(gameState.spriteCache).length}`);
        
        // Update displayed sprite if in combat
        if (gameState.inCombat && elements.enemySprite) {
            elements.enemySprite.src = spritePath;
            elements.enemySprite.style.display = 'block';
        }
        
        return spritePath;
        
    } catch (error) {
        console.error(`✗ Error fetching sprite for "${enemyName}":`, error);
        return null;
    }
}

// Fetch and cache player sprite
async function fetchPlayerSprite(playerName) {
    console.log(`fetchPlayerSprite called for: "${playerName}"`);
    
    // Check if already cached
    if (gameState.playerSprite) {
        console.log(`✓ Using cached player sprite: ${gameState.playerSprite}`);
        return gameState.playerSprite;
    }
    
    console.log(`⟳ Fetching player sprite...`);
    
    try {
        // Use player sprite endpoint
        const result = await apiRequest('/player/sprite', 'POST', {
            player_name: playerName
        });
        
        if (result.error) {
            console.error(`✗ Failed to fetch player sprite:`, result.message);
            // Use default player sprite
            gameState.playerSprite = '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
            
            // Update player avatar in stats panel
            if (elements.playerAvatar) {
                elements.playerAvatar.src = gameState.playerSprite;
            }
            
            return gameState.playerSprite;
        }
        
        const spritePath = result.data.sprite_path;
        console.log(`✓ Matched player sprite: ${spritePath}`);
        
        // Cache the sprite path
        gameState.playerSprite = spritePath;
        
        // Update player avatar in stats panel
        if (elements.playerAvatar) {
            elements.playerAvatar.src = spritePath;
        }
        
        // Update displayed sprite if in combat
        if (gameState.inCombat && elements.playerSprite) {
            elements.playerSprite.src = spritePath;
        }
        
        return spritePath;
        
    } catch (error) {
        console.error(`✗ Error fetching player sprite:`, error);
        // Use default player sprite
        gameState.playerSprite = '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
        
        // Update player avatar in stats panel
        if (elements.playerAvatar) {
            elements.playerAvatar.src = gameState.playerSprite;
        }
        
        return gameState.playerSprite;
    }
}

// Attach event listeners
function attachEventListeners() {
    // Start game
    elements.startGameBtn.addEventListener('click', startNewGame);
    elements.playerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startNewGame();
    });
    
    // Continue game
    if (elements.continueGameBtn) {
        elements.continueGameBtn.addEventListener('click', continueGame);
    }
    if (elements.continueSessionIdInput) {
        elements.continueSessionIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') continueGame();
        });
    }
    
    // Movement
    elements.moveNorth.addEventListener('click', () => movePlayer('north'));
    elements.moveSouth.addEventListener('click', () => movePlayer('south'));
    elements.moveEast.addEventListener('click', () => movePlayer('east'));
    elements.moveWest.addEventListener('click', () => movePlayer('west'));
    elements.moveUp.addEventListener('click', () => movePlayer('up'));
    elements.enterShopBtn.addEventListener('click', openShop);
    elements.enterCasinoBtn.addEventListener('click', openCasino);
    
    // Combat (with animations)
    elements.attackBtn.addEventListener('click', (e) => {
        bounceButton(e.target);
        // Show timing bar instead of attacking directly
        showTimingBar();
    });
    elements.useAllyBtn.addEventListener('click', (e) => {
        bounceButton(e.target);
        showAllyModal();
    });
    elements.useItemBtn.addEventListener('click', (e) => {
        bounceButton(e.target);
        showItemModal();
    });
    elements.fleeBtn.addEventListener('click', (e) => {
        shakeElement(e.target);
        performCombatAction('flee', false);
    });
    
    // Actions
    elements.viewStatsBtn.addEventListener('click', viewStats);
    elements.viewScoresBtn.addEventListener('click', () => showLeaderboardModal());
    elements.submitScoreBtn.addEventListener('click', submitScore);
    if (elements.showSessionBtn) {
        elements.showSessionBtn.addEventListener('click', showSessionId);
    }
    elements.newGameBtn.addEventListener('click', confirmNewGame);
    elements.viewLeaderboardBtn.addEventListener('click', () => showLeaderboardModal());
    
    // Game over
    elements.submitFinalScoreBtn.addEventListener('click', submitScore);
    elements.restartGameBtn.addEventListener('click', () => {
        showScreen('start-screen');
        resetGameState();
    });
    elements.viewFinalLeaderboardBtn.addEventListener('click', () => showLeaderboardModal());
    
    // Ally encounter close button
    if (elements.allyEncounterCloseBtn) {
        elements.allyEncounterCloseBtn.addEventListener('click', () => {
            elements.allyEncounterDisplay.classList.add('hidden');
        });
    }
    
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
    
    // Gear modal
    const openGearMenuBtn = document.getElementById('open-gear-menu-btn');
    if (openGearMenuBtn) {
        openGearMenuBtn.addEventListener('click', openGearModal);
    }
    
    // Gear unequip buttons
    const unequipWeaponBtn = document.getElementById('unequip-weapon-btn');
    const unequipArmorBtn = document.getElementById('unequip-armor-btn');
    const unequipAccessoryBtn = document.getElementById('unequip-accessory-btn');
    
    if (unequipWeaponBtn) {
        unequipWeaponBtn.addEventListener('click', () => unequipGear('weapon'));
    }
    if (unequipArmorBtn) {
        unequipArmorBtn.addEventListener('click', () => unequipGear('armor'));
    }
    if (unequipAccessoryBtn) {
        unequipAccessoryBtn.addEventListener('click', () => unequipGear('accessory'));
    }
    elements.standBtn.addEventListener('click', blackjackStand);
    elements.splitBtn.addEventListener('click', blackjackSplit);
    elements.doubleBtn.addEventListener('click', blackjackDouble);
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
    
    // Prevent multiple simultaneous game starts
    if (!showLoading('Creating adventure...')) {
        return;
    }
    
    addLogEntry('Starting new adventure...', 'important');
    
    const result = await apiRequest('/player/new', 'POST', { name: playerName });
    
    hideLoading();
    
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
    
    // Fetch and cache player sprite
    await fetchPlayerSprite(playerName);
    
    loadLeaderboard();
}

// Continue existing game
async function continueGame() {
    const sessionId = elements.continueSessionIdInput.value.trim();
    
    if (!sessionId) {
        alert('Please enter a session ID');
        return;
    }
    
    await continueGameWithSession(sessionId);
}

async function continueGameWithSession(sessionId) {
    // Prevent multiple simultaneous requests
    if (!showLoading('Loading game...')) {
        return;
    }
    
    addLogEntry('Loading existing game...', 'important');
    
    try {
        const result = await apiRequest('/player/load', 'POST', { session_id: sessionId });
        
        hideLoading();
        
        if (result.error) {
            addLogEntry(`Failed to load game: ${result.message}`, 'danger');
            alert(`Failed to load game: ${result.message}`);
            return;
        }
        
        // Validate response structure
        if (!result.data || !result.data.player) {
            addLogEntry('Invalid game data received', 'danger');
            alert('Invalid game data received. The session may be corrupted.');
            return;
        }
        
        // Check if player is alive
        if (!result.data.player.is_alive) {
            addLogEntry('This character has died. Cannot continue.', 'danger');
            alert('This character has died. You cannot continue with this session.');
            return;
        }
        
        // Set game state
        gameState.sessionId = sessionId;
        gameState.player = result.data.player;
        gameState.currentRoom = result.data.current_room;
        
        // Restore battle state if player was in combat
        if (result.data.player.in_battle && result.data.player.current_enemy) {
            gameState.inCombat = true;
            gameState.currentEnemy = result.data.player.current_enemy;
        } else {
            gameState.inCombat = false;
            gameState.currentEnemy = null;
        }
        
        // Initialize arrays if not present
        if (!gameState.player.allies) gameState.player.allies = [];
        if (!gameState.player.inventory) gameState.player.inventory = [];
        if (!gameState.player.visited_rooms) gameState.player.visited_rooms = [];
        
        // Restore minimap data if available, otherwise initialize with current room
        if (result.data.player.room_positions && Object.keys(result.data.player.room_positions).length > 0) {
            gameState.roomPositions = result.data.player.room_positions;
        } else {
            gameState.roomPositions = {};
            gameState.roomPositions[gameState.player.room_id] = { x: 0, y: 0 };
        }
        
        if (result.data.player.room_info && Object.keys(result.data.player.room_info).length > 0) {
            gameState.roomInfo = result.data.player.room_info;
        } else {
            gameState.roomInfo = {};
            gameState.roomInfo[gameState.player.room_id] = {
                hasStairs: gameState.currentRoom.has_staircase || false,
                isShop: gameState.currentRoom.is_shop || false
            };
        }
        
        showScreen('game-screen');
        updatePlayerDisplay();
        updateRoomDisplay();
        updateMinimap();
        addLogEntry('Game loaded successfully!', 'success');
        addLogEntry(gameState.currentRoom.description);
        
        // Fetch and cache player sprite first (needed for combat display)
        await fetchPlayerSprite(gameState.player.name);
        
        // Restore combat if player was in battle
        if (gameState.inCombat && gameState.currentEnemy) {
            addLogEntry('Resuming battle...', 'important');
            
            // Fetch enemy sprite before showing combat area
            if (gameState.currentEnemy.name && gameState.currentEnemy.description) {
                await fetchEnemySprite(gameState.currentEnemy.name, gameState.currentEnemy.description);
            }
            
            // showCombatArea() will display all combat UI including enemy stats and sprites
            showCombatArea();
        }
        
        loadLeaderboard();
        
    } catch (error) {
        hideLoading();
        addLogEntry(`Error loading game: ${error.message}`, 'danger');
        alert(`Error loading game: ${error.message}`);
    }
}

/**
 * Refresh all game displays - called by dev tools after making changes
 */
async function refreshGameDisplay() {
    console.log('refreshGameDisplay called!');
    
    if (!gameState.sessionId) {
        console.log('No session to refresh');
        return;
    }
    
    console.log('Reloading player data for session:', gameState.sessionId);
    
    try {
        // Reload player data from server
        const result = await apiRequest('/player/load', 'POST', { session_id: gameState.sessionId });
        
        console.log('Player reload result:', result);
        
        if (!result.success) {
            console.error('Failed to reload player data:', result.message);
            return;
        }
        
        // Update game state
        gameState.player = result.data.player;
        gameState.currentRoom = result.data.current_room;
        
        console.log('Updated player:', gameState.player);
        console.log('Updated room:', gameState.currentRoom);
        
        // Update battle state
        if (result.data.player.in_battle && result.data.player.current_enemy) {
            gameState.inCombat = true;
            gameState.currentEnemy = result.data.player.current_enemy;
        } else {
            gameState.inCombat = false;
            gameState.currentEnemy = null;
        }
        
        // Initialize arrays if not present
        if (!gameState.player.allies) gameState.player.allies = [];
        if (!gameState.player.inventory) gameState.player.inventory = [];
        if (!gameState.player.visited_rooms) gameState.player.visited_rooms = [];
        
        // Update minimap data
        if (result.data.player.room_positions) {
            gameState.roomPositions = result.data.player.room_positions;
        }
        if (result.data.player.room_info) {
            gameState.roomInfo = result.data.player.room_info;
        }
        
        console.log('Updating displays...');
        
        // Refresh all displays
        updatePlayerDisplay();
        console.log('Player display updated');
        
        updateRoomDisplay();
        console.log('Room display updated');
        
        updateMinimap();
        console.log('Minimap updated');
        
        // If in combat, refresh combat display
        if (gameState.inCombat && gameState.currentEnemy) {
            await showCombatArea();
            console.log('Combat display updated');
        }
        
        console.log('✅ Game display refreshed successfully');
    } catch (error) {
        console.error('❌ Error refreshing game display:', error);
    }
}

// Make refresh function globally accessible for dev tools
window.refreshGameDisplay = refreshGameDisplay;
console.log('refreshGameDisplay function registered on window');

// Show session ID
function showSessionId() {
    if (!gameState.sessionId) {
        alert('No active game session');
        return;
    }
    
    const message = `Your Session ID:\n\n${gameState.sessionId}\n\nSave this ID to continue your game later!`;
    
    // Copy to clipboard
    navigator.clipboard.writeText(gameState.sessionId).then(() => {
        alert(message + '\n\n✅ Copied to clipboard!');
    }).catch(() => {
        alert(message);
    });
}

// Update player display
function updatePlayerDisplay() {
    if (!gameState.player) return;
    
    elements.playerNameDisplay.textContent = gameState.player.name;
    
    // Parse health - handle both number and "50/100" string format
    let currentHealth, maxHealth;
    if (typeof gameState.player.health === 'string' && gameState.player.health.includes('/')) {
        const healthParts = gameState.player.health.split('/');
        currentHealth = parseInt(healthParts[0]);
        maxHealth = parseInt(healthParts[1]);
    } else {
        currentHealth = parseInt(gameState.player.health);
        maxHealth = parseInt(gameState.player.max_health || 100);
    }
    
    const healthPercent = (currentHealth / maxHealth) * 100;
    
    // Detect health change and animate
    const oldHealth = elements.healthBar.dataset.currentHealth || currentHealth;
    if (currentHealth < oldHealth) {
        animateDamage(elements.healthBar.parentElement);
        shakeElement(document.querySelector('.stat-card:first-child'));
    } else if (currentHealth > oldHealth) {
        animateHealing(elements.healthBar.parentElement);
        pulseElement(document.querySelector('.stat-card:first-child'));
    }
    elements.healthBar.dataset.currentHealth = currentHealth;
    
    // Add low health warning
    if (healthPercent < 30) {
        elements.healthBar.classList.add('low-health');
    } else {
        elements.healthBar.classList.remove('low-health');
    }
    
    elements.healthBar.style.width = `${healthPercent}%`;
    elements.healthText.textContent = `${currentHealth}/${maxHealth}`;
    
    // Detect gold change and animate
    const oldGold = elements.playerGold.dataset.value || gameState.player.gold;
    if (gameState.player.gold !== parseInt(oldGold)) {
        animateGoldChange(elements.playerGold);
    }
    elements.playerGold.dataset.value = gameState.player.gold;
    elements.playerGold.textContent = gameState.player.gold;
    
    // Detect level change and animate
    const oldLevel = elements.playerLevel.dataset.value || gameState.player.level;
    if (gameState.player.level > parseInt(oldLevel)) {
        animateLevelUp(elements.playerLevel.parentElement);
        addLogEntry('🎉 LEVEL UP! You feel more powerful!', 'success');
        createParticles(
            elements.playerLevel.getBoundingClientRect().left + 20,
            elements.playerLevel.getBoundingClientRect().top + 10,
            '#ffd700',
            15
        );
    }
    elements.playerLevel.dataset.value = gameState.player.level;
    elements.playerLevel.textContent = gameState.player.level || 1;
    
    elements.playerFloor.textContent = gameState.player.floor;
    elements.playerAllies.textContent = gameState.player.allies ? gameState.player.allies.length : 0;
    
    // Update player ailments display
    const playerAilmentsEl = document.getElementById('player-ailments');
    if (playerAilmentsEl) {
        if (gameState.player.ailments && gameState.player.ailments.length > 0) {
            // Display ailments with severity as superscript
            const ailmentDisplay = gameState.player.ailments.map(a => {
                const emoji = a.emoji || '';
                const severity = a.severity !== undefined ? a.severity : '?';
                return `${emoji}${severity}`;
            }).join(' ');
            playerAilmentsEl.textContent = ailmentDisplay;
            
            // Create tooltip with full ailment details
            const tooltipText = gameState.player.ailments.map(a => 
                `${a.name || a.type} (Severity ${a.severity}, ${a.turns_remaining}/${a.duration} turns)`
            ).join(', ');
            playerAilmentsEl.title = tooltipText;
            
            console.log('Player ailments displayed:', ailmentDisplay, tooltipText);
        } else {
            playerAilmentsEl.textContent = '';
            playerAilmentsEl.title = '';
        }
    }
    
    // Update player element display with dual elements
    const playerAttackElementEl = document.getElementById('player-attack-element');
    const playerDefenseElementEl = document.getElementById('player-defense-element');
    
    if (playerAttackElementEl && gameState.player.attack_element) {
        const elementEmoji = getElementEmoji(gameState.player.attack_element);
        const elementName = formatElementName(gameState.player.attack_element);
        playerAttackElementEl.textContent = `${elementName}`;
        playerAttackElementEl.className = `element-badge element-${gameState.player.attack_element}`;
        playerAttackElementEl.title = `Attack Element: ${elementName}`;
    }
    
    if (playerDefenseElementEl && gameState.player.defense_element) {
        const elementEmoji = getElementEmoji(gameState.player.defense_element);
        const elementName = formatElementName(gameState.player.defense_element);
        playerDefenseElementEl.textContent = `${elementName}`;
        playerDefenseElementEl.className = `element-badge element-${gameState.player.defense_element}`;
        playerDefenseElementEl.title = `Defense Element: ${elementName}`;
    }
    
    // Update stats with gear modifiers and ailment indicators
    const getStatAilmentIndicator = (ailmentType) => {
        if (!gameState.player.ailments) return '';
        for (const ailment of gameState.player.ailments) {
            if (ailment.type === ailmentType) {
                const statEmoji = ailment.type === 'weakened' ? '💔' : 
                                 ailment.type === 'irradiated' ? '☢️' : 
                                 ailment.type === 'shackled' ? '⛓️' : '';
                return statEmoji ? ` ${statEmoji}` : '';
            }
        }
        return '';
    };
    
    // Show base stats with gear modifiers
    if (gameState.player.total_stats) {
        const stats = gameState.player.total_stats;
        
        elements.playerAttack.textContent = stats.attack.base + getStatAilmentIndicator('weakened');
        const attackModifierEl = document.getElementById('player-attack-modifier');
        if (attackModifierEl && stats.attack.gear > 0) {
            attackModifierEl.textContent = `(+${stats.attack.gear})`;
            attackModifierEl.className = 'stat-modifier positive';
        } else if (attackModifierEl) {
            attackModifierEl.textContent = '';
        }
        
        elements.playerDefense.textContent = stats.defense.base + getStatAilmentIndicator('irradiated');
        const defenseModifierEl = document.getElementById('player-defense-modifier');
        if (defenseModifierEl && stats.defense.gear > 0) {
            defenseModifierEl.textContent = `(+${stats.defense.gear})`;
            defenseModifierEl.className = 'stat-modifier positive';
        } else if (defenseModifierEl) {
            defenseModifierEl.textContent = '';
        }
        
        elements.playerSpeed.textContent = stats.speed.base + getStatAilmentIndicator('shackled');
        const speedModifierEl = document.getElementById('player-speed-modifier');
        if (speedModifierEl && stats.speed.gear !== 0) {
            speedModifierEl.textContent = stats.speed.gear > 0 ? `(+${stats.speed.gear})` : `(${stats.speed.gear})`;
            speedModifierEl.className = stats.speed.gear > 0 ? 'stat-modifier positive' : 'stat-modifier negative';
        } else if (speedModifierEl) {
            speedModifierEl.textContent = '';
        }
    } else {
        // Fallback to old display if total_stats not available
        elements.playerAttack.textContent = (gameState.player.attack_power || 10) + getStatAilmentIndicator('weakened');
        elements.playerDefense.textContent = (gameState.player.defense || 5) + getStatAilmentIndicator('irradiated');
        elements.playerSpeed.textContent = (gameState.player.speed || 10) + getStatAilmentIndicator('shackled');
    }
    
    // Update allies list
    updateAlliesList();
    
    // Update inventory display
    updateInventoryDisplay();
}

// Update allies list
function updateAlliesList() {
    const alliesList = elements.alliesList;
    
    console.log('DEBUG updateAlliesList: player exists?', !!gameState.player);
    console.log('DEBUG updateAlliesList: allies array?', gameState.player?.allies);
    console.log('DEBUG updateAlliesList: allies length?', gameState.player?.allies?.length);
    
    if (!gameState.player || !gameState.player.allies || gameState.player.allies.length === 0) {
        alliesList.innerHTML = '<p class="empty-state">No allies recruited yet</p>';
        return;
    }
    
    // Filter out allies with no uses remaining
    const availableAllies = gameState.player.allies.filter(ally => ally.uses_remaining > 0);
    
    if (availableAllies.length === 0) {
        alliesList.innerHTML = '<p class="empty-state">No allies available (all have been exhausted)</p>';
        return;
    }
    
    // Display actual ally details with usage count
    alliesList.innerHTML = availableAllies.map((ally, index) => {
        // Find the original index in the full allies array
        const originalIndex = gameState.player.allies.indexOf(ally);
        const typeEmoji = {
            'healer': '💚',
            'attacker': '⚔️',
            'skipper': '⏸️',
            'caster_poison': '🧪',
            'caster_paralysis': '⚡'
        };
        
        const usesText = ally.uses_remaining !== undefined 
            ? `${ally.uses_remaining}/${ally.max_uses || 3}`
            : '3/3';
        
        const typeValue = ally.type === 'skipper' ? 'Skip Turn' : 
                         ally.type === 'healer' ? `+${ally.value} HP` :
                         ally.type === 'caster_poison' ? `🧪 Poison (Sev ${ally.value})` :
                         ally.type === 'caster_paralysis' ? `⚡ Paralyze (Sev ${ally.value})` :
                         `${ally.value} DMG`;
        
        // Add element badge if ally has an element (attackers/casters)
        let elementBadge = '';
        if (ally.element) {
            const elementEmoji = getElementEmoji(ally.element);
            const elementName = formatElementName(ally.element);
            
            // Determine color based on effectiveness vs current enemy
            let elementClass = 'element-badge-neutral';
            let effectivenessText = '';
            if (gameState.inCombat && gameState.currentEnemy && gameState.currentEnemy.element) {
                const advantage = getElementAdvantage(ally.element, gameState.currentEnemy.element);
                if (advantage === 'advantage') {
                    elementClass = 'element-badge-effective';
                    effectivenessText = ' (Effective!)';
                } else if (advantage === 'disadvantage') {
                    elementClass = 'element-badge-weak';
                    effectivenessText = ' (Weak!)';
                }
            }
            
            elementBadge = `<span class="ally-element-badge ${elementClass}" title="${elementName}${effectivenessText}">${elementEmoji} ${elementName}</span>`;
        }
        
        return `
            <div class="ally-card clickable" data-ally-index="${originalIndex}" onclick="showAllyDetails(${originalIndex})">
                <div class="ally-header">
                    <span class="ally-icon">${typeEmoji[ally.type] || '🤝'}</span>
                    <span class="ally-name">${ally.name}</span>
                    ${elementBadge}
                </div>
                <div class="ally-info-row">
                    <span class="ally-type">${ally.type}</span>
                    <span class="ally-uses">Uses: ${usesText}</span>
                </div>
                <div class="ally-value">${typeValue}</div>
            </div>
        `;
    }).join('');
}

// Show ally details in a modal
function showAllyDetails(allyIndex) {
    if (!gameState.player || !gameState.player.allies || allyIndex >= gameState.player.allies.length) {
        return;
    }
    
    const ally = gameState.player.allies[allyIndex];
    
    // Use the existing ally encounter display
    if (!elements.allyEncounterDisplay) return;
    
    const spritePath = ally.sprite ? `/static/sprites/${ally.sprite}` : '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
    
    const typeEmoji = {
        'healer': '💚',
        'attacker': '⚔️',
        'skipper': '⏸️',
        'caster_poison': '🧪',
        'caster_paralysis': '⚡'
    };
    
    const typeDescription = {
        'healer': `Heals ${ally.value} HP`,
        'attacker': `Deals ${ally.value} damage`,
        'skipper': 'Skips enemy turn for 2 rounds',
        'caster_poison': `Inflicts Poison (Severity ${ally.value})`,
        'caster_paralysis': `Inflicts Paralysis (Severity ${ally.value})`
    };
    
    const usesText = ally.uses_remaining !== undefined 
        ? `${ally.uses_remaining}/${ally.max_uses || 3} uses remaining`
        : '3/3 uses remaining';
    
    // Update the display elements
    elements.allyEncounterName.textContent = `${typeEmoji[ally.type] || '🤝'} ${ally.name}`;
    elements.allyEncounterDescription.innerHTML = `
        <div style="text-align: center;">
            <div style="color: #6aa3d0; font-size: 1.1rem; font-weight: bold; margin: 15px 0;">
                ${ally.type.toUpperCase()}: ${typeDescription[ally.type]}
            </div>
            <div style="color: var(--accent-info); font-size: 1rem; font-weight: bold; margin: 10px 0;">
                ${usesText}
            </div>
            <div style="color: var(--text-secondary); font-style: italic; margin: 20px 0; line-height: 1.6;">
                ${ally.description || 'A helpful ally.'}
            </div>
            <button class="btn btn-danger" onclick="confirmFireAlly(${allyIndex})" style="margin-top: 10px;">Fire Ally</button>
        </div>
    `;
    elements.allyEncounterSprite.src = spritePath;
    
    // Change the close button to just close (not fire)
    elements.allyEncounterCloseBtn.onclick = () => {
        elements.allyEncounterDisplay.classList.add('hidden');
    };
    
    // Show the display
    elements.allyEncounterDisplay.classList.remove('hidden');
}

function closeAllyDetails() {
    if (elements.allyEncounterDisplay) {
        elements.allyEncounterDisplay.classList.add('hidden');
    }
}

function confirmFireAlly(allyIndex) {
    closeAllyDetails();
    fireAlly(allyIndex);
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
        
        // Determine icon based on gear type or rarity
        let itemIcon;
        if (item.gear_type) {
            // Gear items use type-specific emojis
            const gearEmoji = {
                'weapon': '🗡️',
                'armor': '🛡️',
                'accessory': '💍'
            };
            itemIcon = gearEmoji[item.gear_type] || '⚪';
        } else {
            // Regular items use rarity emoji
            itemIcon = rarityEmoji[item.rarity] || '⚪';
        }
        
        // Create detailed tooltip text
        let tooltipText;
        if (item.gear_type) {
            // Gear tooltip
            tooltipText = `${item.description || item.name}\n\nType: ${item.gear_type}\nRarity: ${item.rarity || 'common'}`;
            if (item.attack_bonus) tooltipText += `\n⚔️ Attack: +${item.attack_bonus}`;
            if (item.defense_bonus) tooltipText += `\n🛡️ Defense: +${item.defense_bonus}`;
            if (item.speed_bonus) tooltipText += `\n⚡ Speed: ${item.speed_bonus > 0 ? '+' : ''}${item.speed_bonus}`;
            if (item.element) tooltipText += `\n🌟 Element: ${item.element}`;
        } else {
            // Item tooltip
            tooltipText = `${item.description || item.name}\n\nEffect: ${item.effect_type || 'unknown'}\nValue: ${item.effect_value || 0}\nRarity: ${item.rarity || 'common'}${item.usable_in_combat ? '\n✓ Can use in combat' : '\n✗ Cannot use in combat'}`;
        }
        
        return `
            <div class="item-entry" data-tooltip="${tooltipText}" title="${item.description || item.name}">
                <span class="item-icon">${itemIcon}</span>
                <span class="item-name">${item.name}</span>
            </div>
        `;
    }).join('');
}

// Update ailment displays for both player and enemy
function updateAilmentDisplays() {
    console.log('updateAilmentDisplays called');
    
    // Update player ailments
    const playerAilmentsEl = document.getElementById('player-ailments');
    if (playerAilmentsEl && gameState.player) {
        if (gameState.player.ailments && gameState.player.ailments.length > 0) {
            // Display ailments with severity as superscript
            const ailmentDisplay = gameState.player.ailments.map(a => {
                const emoji = a.emoji || '';
                const severity = a.severity !== undefined ? a.severity : '?';
                return `${emoji}${severity}`;
            }).join(' ');
            playerAilmentsEl.textContent = ailmentDisplay;
            
            // Create tooltip with full ailment details
            const tooltipText = gameState.player.ailments.map(a => 
                `${a.name || a.type} (Severity ${a.severity}, ${a.turns_remaining}/${a.duration} turns)`
            ).join(', ');
            playerAilmentsEl.title = tooltipText;
            
            console.log('Player ailments updated:', ailmentDisplay, tooltipText);
        } else {
            playerAilmentsEl.textContent = '';
            playerAilmentsEl.title = '';
        }
    }
    
    // Update enemy ailments
    const enemyAilmentsEl = document.getElementById('enemy-ailments');
    if (enemyAilmentsEl && gameState.currentEnemy) {
        if (gameState.currentEnemy.ailments && gameState.currentEnemy.ailments.length > 0) {
            // Display ailments with severity as superscript
            const ailmentDisplay = gameState.currentEnemy.ailments.map(a => {
                const emoji = a.emoji || '';
                const severity = a.severity !== undefined ? a.severity : '?';
                return `${emoji}${severity}`;
            }).join(' ');
            enemyAilmentsEl.textContent = ailmentDisplay;
            
            // Create tooltip with full ailment details
            const tooltipText = gameState.currentEnemy.ailments.map(a => 
                `${a.name || a.type} (Severity ${a.severity}, ${a.turns_remaining}/${a.duration} turns)`
            ).join(', ');
            enemyAilmentsEl.title = tooltipText;
            
            console.log('Enemy ailments updated:', ailmentDisplay, tooltipText, gameState.currentEnemy.ailments);
        } else {
            enemyAilmentsEl.textContent = '';
            enemyAilmentsEl.title = '';
            console.log('Enemy has no ailments or empty array');
        }
    }
    
    // Update enemy can-inflict indicator
    const enemyCanInflictEl = document.getElementById('enemy-can-inflict');
    if (enemyCanInflictEl && gameState.currentEnemy) {
        // Check for both new multi-type and old single-type format
        const ailmentTypes = gameState.currentEnemy.ailment_inflict_types || 
                           (gameState.currentEnemy.ailment_inflict_type ? [gameState.currentEnemy.ailment_inflict_type] : []);
        
        if (ailmentTypes.length > 0 && gameState.currentEnemy.ailment_inflict_chance > 0) {
            // Map ailment types to their emojis
            const ailmentEmojiMap = {
                'poison': '🧪',
                'paralysis': '⚡',
                'weakened': '💔',
                'irradiated': '☢️',
                'shackled': '⛓️',
                'infatuated': '💖',
                'blinded': '🙈'
            };
            
            // Get emojis for all ailment types
            const ailmentEmojis = ailmentTypes.map(type => ailmentEmojiMap[type] || '❓').join('');
            const chance = Math.round(gameState.currentEnemy.ailment_inflict_chance * 100);
            enemyCanInflictEl.textContent = `${ailmentEmojis} ${chance}%`;
            enemyCanInflictEl.style.display = 'inline';
            
            // Show all types in tooltip
            const typesList = ailmentTypes.join(', ');
            let tooltipText = `Can inflict ${typesList} (${chance}% chance each)`;
            if (gameState.currentEnemy.ailment_inflict_severity !== undefined && gameState.currentEnemy.ailment_inflict_severity !== null) {
                tooltipText += ` - Severity ${gameState.currentEnemy.ailment_inflict_severity}`;
            }
            enemyCanInflictEl.title = tooltipText;
            
            console.log('Enemy can inflict:', typesList, chance + '%', 
                       gameState.currentEnemy.ailment_inflict_severity !== null ? `Severity ${gameState.currentEnemy.ailment_inflict_severity}` : '(floor-based)');
        } else {
            enemyCanInflictEl.style.display = 'none';
        }
    }
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
    
    // Prevent multiple simultaneous item uses
    if (!showLoading('Using item...')) {
        return;
    }
    
    addLogEntry('Using item...', 'info');
    
    const result = await apiRequest('/inventory/use', 'POST', {
        session_id: gameState.sessionId,
        item_id: itemId
    });
    
    hideLoading();
    
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

// ============================================
// TIMING BAR MINI-GAME
// ============================================

/**
 * Show the timing bar modal and start the mini-game
 */
function showTimingBar() {
    console.log('showTimingBar called');
    console.log('timingBarModal element:', elements.timingBarModal);
    
    if (!elements.timingBarModal) {
        console.error('Timing bar modal not found!');
        return;
    }
    
    // Calculate timing bar speed based on player vs enemy speed
    const playerSpeed = gameState.player?.speed || 10;
    const enemySpeed = gameState.currentEnemy?.speed || 10;
    const speedDifference = enemySpeed - playerSpeed;
    
    // Base speed is 2.0
    // For each point the enemy is faster, increase speed by 0.15
    // For each point the player is faster, decrease speed by 0.15
    // Min speed: 1.0, Max speed: 4.0
    const baseSpeed = 2.0;
    const speedModifier = speedDifference * 0.15;
    gameState.timingBarSpeed = Math.max(1.0, Math.min(4.0, baseSpeed + speedModifier));
    
    console.log(`Timing bar speed: ${gameState.timingBarSpeed.toFixed(2)} (Player: ${playerSpeed}, Enemy: ${enemySpeed}, Diff: ${speedDifference})`);
    
    // Reset timing bar state
    gameState.timingBarPosition = 0;
    gameState.timingBarDirection = 1;
    gameState.timingBarActive = true;
    
    // Show modal
    console.log('Adding active class to timing bar modal');
    elements.timingBarModal.classList.add('active');
    console.log('Modal classList after add:', elements.timingBarModal.classList.toString());
    
    // Reset indicator position
    if (elements.timingIndicator) {
        elements.timingIndicator.style.left = '0%';
    } else {
        console.error('Timing indicator element not found!');
    }
    
    // Update multiplier text
    if (elements.timingMultiplierText) {
        elements.timingMultiplierText.innerHTML = 'Multiplier: <strong>?</strong>';
    } else {
        console.error('Timing multiplier text element not found!');
    }
    
    // Start animation
    startTimingBarAnimation();
    
    // Add keyboard listener
    document.addEventListener('keydown', handleTimingBarKeypress);
}

/**
 * Start the timing bar animation
 */
function startTimingBarAnimation() {
    // Clear any existing interval
    if (gameState.timingBarInterval) {
        clearInterval(gameState.timingBarInterval);
    }
    
    gameState.timingBarInterval = setInterval(() => {
        if (!gameState.timingBarActive) {
            clearInterval(gameState.timingBarInterval);
            return;
        }
        
        // Update position
        gameState.timingBarPosition += gameState.timingBarSpeed * gameState.timingBarDirection;
        
        // Bounce at edges
        if (gameState.timingBarPosition >= 100) {
            gameState.timingBarPosition = 100;
            gameState.timingBarDirection = -1;
        } else if (gameState.timingBarPosition <= 0) {
            gameState.timingBarPosition = 0;
            gameState.timingBarDirection = 1;
        }
        
        // Update indicator position
        if (elements.timingIndicator) {
            elements.timingIndicator.style.left = `${gameState.timingBarPosition}%`;
        }
    }, 16); // ~60 FPS
}

/**
 * Handle keypress during timing bar mini-game
 */
function handleTimingBarKeypress(e) {
    if (!gameState.timingBarActive) return;
    
    if (e.code === 'Space' || e.key === ' ') {
        e.preventDefault();
        stopTimingBar();
    }
}

/**
 * Stop the timing bar and calculate multiplier
 */
function stopTimingBar() {
    gameState.timingBarActive = false;
    
    // Clear interval
    if (gameState.timingBarInterval) {
        clearInterval(gameState.timingBarInterval);
        gameState.timingBarInterval = null;
    }
    
    // Remove keyboard listener
    document.removeEventListener('keydown', handleTimingBarKeypress);
    
    // Calculate multiplier based on position
    const position = gameState.timingBarPosition;
    const multiplier = calculateTimingMultiplier(position);
    
    // Update display
    if (elements.timingMultiplierText) {
        const multiplierText = multiplier.toFixed(2) + 'x';
        const color = multiplier >= 1.15 ? '#ffd700' : multiplier >= 1.0 ? '#4a90e2' : multiplier >= 0.9 ? '#f39c12' : '#e74c3c';
        elements.timingMultiplierText.innerHTML = `Multiplier: <strong style="color: ${color}">${multiplierText}</strong>`;
    }
    
    // Wait a moment to show the result, then perform attack
    setTimeout(() => {
        hideTimingBar();
        performCombatAction('attack', false, null, multiplier);
    }, 800);
}

/**
 * Calculate damage multiplier based on timing bar position
 * Zones: 0-11% = 0.7x, 11-32% = 0.9x, 32-47% = 1.0x, 47-53% = 1.15x,
 *        53-68% = 1.0x, 68-89% = 0.9x, 89-100% = 0.7x
 */
function calculateTimingMultiplier(position) {
    if (position >= 47 && position <= 53) {
        // Perfect zone (6% in the middle)
        return 1.15;
    } else if ((position >= 32 && position < 47) || (position > 53 && position <= 68)) {
        // Normal zone (15% on each side of perfect)
        return 1.0;
    } else if ((position >= 11 && position < 32) || (position > 68 && position <= 89)) {
        // Good zone (21% on each side)
        return 0.9;
    } else {
        // Poor zone (11% on each end)
        return 0.7;
    }
}

/**
 * Hide the timing bar modal
 */
function hideTimingBar() {
    if (elements.timingBarModal) {
        elements.timingBarModal.classList.remove('active');
    }
    
    // Ensure animation is stopped
    if (gameState.timingBarInterval) {
        clearInterval(gameState.timingBarInterval);
        gameState.timingBarInterval = null;
    }
    
    // Remove keyboard listener (in case it's still there)
    document.removeEventListener('keydown', handleTimingBarKeypress);
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
        
        const spritePath = ally.sprite ? `/static/sprites/${ally.sprite}` : '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
        
        const usesText = ally.uses_remaining !== undefined 
            ? `${ally.uses_remaining}/${ally.max_uses || 3} uses left`
            : '3/3 uses left';
        
        const isDisabled = ally.uses_remaining === 0 || ally.used ? 'disabled' : '';
        
        // Add element badge if ally has an element
        let elementBadge = '';
        if (ally.element) {
            const elementEmoji = getElementEmoji(ally.element);
            const elementName = formatElementName(ally.element);
            
            // Determine color based on effectiveness vs current enemy
            let elementClass = 'element-badge-neutral';
            let effectivenessText = '';
            if (gameState.currentEnemy && gameState.currentEnemy.element) {
                const advantage = getElementAdvantage(ally.element, gameState.currentEnemy.element);
                if (advantage === 'advantage') {
                    elementClass = 'element-badge-effective';
                    effectivenessText = ' (Effective!)';
                } else if (advantage === 'disadvantage') {
                    elementClass = 'element-badge-weak';
                    effectivenessText = ' (Weak!)';
                }
            }
            
            elementBadge = `<span class="ally-element-badge ${elementClass}" title="${elementName}${effectivenessText}">${elementEmoji} ${elementName}</span>`;
        }
        
        return `
            <div class="ally-card ${isDisabled}" data-ally-index="${index}">
                <div class="ally-sprite-preview">
                    <img src="${spritePath}" alt="${ally.name}" />
                </div>
                <div class="ally-header">
                    <span class="ally-icon">${typeEmoji[ally.type] || '👤'}</span>
                    <span class="ally-title">${ally.name}</span>
                    ${elementBadge}
                </div>
                <div class="ally-description">${ally.description || typeDescription[ally.type]}</div>
                <div class="ally-stats">
                    <span class="ally-type">${ally.type}</span>
                    <span class="ally-value">${typeDescription[ally.type]}</span>
                </div>
                <div class="ally-uses">${usesText}</div>
                <div class="ally-card-buttons">
                    <button class="btn btn-primary btn-use-ally" data-ally-index="${index}" ${isDisabled}>Call Ally</button>
                    <button class="btn btn-danger btn-fire-ally" data-ally-index="${index}">Fire</button>
                </div>
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
    
    // Attach click handlers to fire buttons
    allyList.querySelectorAll('.btn-fire-ally').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const allyIndex = parseInt(e.target.getAttribute('data-ally-index'));
            fireAlly(allyIndex);
        });
    });
    
    // Attach click handlers to view details buttons
    allyList.querySelectorAll('.btn-view-ally').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const allyIndex = parseInt(e.target.getAttribute('data-ally-index'));
            const ally = gameState.player.allies[allyIndex];
            if (ally) {
                showAllyDetailModal(ally);
            }
        });
    });
}

// Show ally encounter display with sprite
function showAllyEncounter(ally) {
    if (!ally || !elements.allyEncounterDisplay) return;
    
    const spritePath = ally.sprite ? `/static/sprites/${ally.sprite}` : '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
    
    elements.allyEncounterName.textContent = ally.name || 'New Ally';
    elements.allyEncounterDescription.textContent = ally.description || 'A helpful ally joins you!';
    elements.allyEncounterSprite.src = spritePath;
    
    elements.allyEncounterDisplay.classList.remove('hidden');
}

// Show ally detail modal
function showAllyDetailModal(ally) {
    if (!ally || !elements.allyDetailModal) return;
    
    const spritePath = ally.sprite ? `/static/sprites/${ally.sprite}` : '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
    
    const typeEmoji = {
        'healer': '💚 Healer',
        'attacker': '⚔️ Attacker',
        'skipper': '⏸️ Skipper'
    };
    
    const typeDescription = {
        'healer': `Heals ${ally.value} HP`,
        'attacker': `Deals ${ally.value} damage`,
        'skipper': 'Skips enemy turn'
    };
    
    elements.allyDetailName.textContent = ally.name || 'Ally';
    elements.allyDetailType.textContent = typeEmoji[ally.type] || ally.type;
    elements.allyDetailValue.textContent = typeDescription[ally.type] || ally.value;
    elements.allyDetailDescription.textContent = ally.description || 'A helpful ally.';
    elements.allyDetailSprite.src = spritePath;
    
    elements.allyDetailModal.classList.add('active');
}

// Use an ally
async function useAlly(allyIndex) {
    elements.allyModal.classList.remove('active');
    
    addLogEntry('Calling ally...', 'info');
    
    // Get ally info before using
    const ally = gameState.player.allies[allyIndex];
    if (ally) {
        // Show ally sprite in combat and play animation
        showCombatAllySprite(ally);
    }
    
    await performCombatAction('attack', false, allyIndex);
}

// Fire (remove) an ally from party
async function fireAlly(allyIndex) {
    console.log('DEBUG fireAlly: Starting with allyIndex:', allyIndex);
    console.log('DEBUG fireAlly: Current allies:', gameState.player.allies);
    
    const ally = gameState.player.allies[allyIndex];
    if (!ally) {
        console.log('DEBUG fireAlly: No ally found at index', allyIndex);
        return;
    }
    
    console.log('DEBUG fireAlly: Attempting to fire:', ally.name);
    
    if (!confirm(`Are you sure you want to fire ${ally.name}? They will be removed from your party permanently.`)) {
        console.log('DEBUG fireAlly: User cancelled');
        return;
    }
    
    try {
        console.log('DEBUG fireAlly: Sending request to server...');
        const response = await fetch('/api/player/fire-ally', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: gameState.sessionId,
                ally_index: allyIndex
            })
        });
        
        console.log('DEBUG fireAlly: Response status:', response.status);
        const data = await response.json();
        console.log('DEBUG fireAlly: Response data:', data);
        
        if (!data.error) {
            console.log('DEBUG fireAlly: Success! New allies:', data.data.allies);
            addLogEntry(data.message, 'info');
            
            // Update the allies array with the returned data
            gameState.player.allies = data.data.allies.map(allyData => ({
                name: allyData.name,
                type: allyData.type,
                value: allyData.value,
                description: allyData.description,
                sprite: allyData.sprite,
                uses_remaining: allyData.uses_remaining,
                max_uses: allyData.max_uses,
                used: allyData.used
            }));
            
            console.log('DEBUG fireAlly: Updated gameState.player.allies:', gameState.player.allies);
            
            // Update allies list display
            updateAlliesList();
            
            // Close the detail overlay
            if (elements.allyEncounterDisplay) {
                elements.allyEncounterDisplay.classList.add('hidden');
            }
            
            // Close and reopen modal to refresh if there are still allies
            elements.allyModal.classList.remove('active');
            if (gameState.player.allies.length > 0) {
                setTimeout(() => showAllyModal(), 100);
            }
        } else {
            console.log('DEBUG fireAlly: Server returned error:', data.message);
            addLogEntry(`Error: ${data.message}`, 'danger');
        }
    } catch (error) {
        console.error('DEBUG fireAlly: Exception caught:', error);
        addLogEntry('Failed to fire ally: ' + (error.message || 'Unknown error'), 'danger');
    }
}

// Show ally sprite in combat area with animation
function showCombatAllySprite(ally) {
    if (!ally || !elements.allySpriteContainer || !elements.allySprite) return;
    
    const spritePath = ally.sprite ? `/static/sprites/${ally.sprite}` : '/static/sprites/player_knight_dog_sword_shield_armor_warrior_great.png';
    
    elements.allySprite.src = spritePath;
    elements.allySpriteContainer.classList.remove('hidden');
    
    // Remove any existing animation classes
    elements.allySprite.classList.remove('ally-animation-healer', 'ally-animation-attacker', 'ally-animation-skipper');
    
    // Add animation based on ally type
    setTimeout(() => {
        const animationClass = `ally-animation-${ally.type}`;
        elements.allySprite.classList.add(animationClass);
        
        // Hide ally sprite after animation (2-3 seconds)
        setTimeout(() => {
            hideCombatAllySprite();
        }, 3000);
    }, 100);
}

// Hide ally sprite from combat area
function hideCombatAllySprite() {
    if (elements.allySpriteContainer) {
        elements.allySpriteContainer.classList.add('hidden');
    }
    if (elements.allySprite) {
        elements.allySprite.classList.remove('ally-animation-healer', 'ally-animation-attacker', 'ally-animation-skipper');
    }
}

// Update room display
function updateRoomDisplay() {
    if (!gameState.currentRoom) return;
    
    if (elements.roomName) {
        elements.roomName.textContent = gameState.currentRoom.name || 'Unknown Room';
    }
    if (elements.roomDescription) {
        // Just display the description as-is (ally hint is now added server-side on floor generation)
        elements.roomDescription.textContent = gameState.currentRoom.description || 'A mysterious room...';
    }
    
    // Update room features
    if (elements.roomFeatures) {
        elements.roomFeatures.innerHTML = '';
        
        if (gameState.currentRoom.has_staircase) {
            const badge = document.createElement('span');
            badge.className = 'feature-badge';
            badge.textContent = '� Staircase Available';
            elements.roomFeatures.appendChild(badge);
        }
        
        if (gameState.currentRoom.has_been_visited) {
            const badge = document.createElement('span');
            badge.className = 'feature-badge';
            badge.textContent = '👁️ Previously Visited';
            elements.roomFeatures.appendChild(badge);
        }
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
    // Prevent multiple simultaneous moves
    if (!showLoading('Moving...')) {
        return;
    }
    
    addLogEntry(`Moving ${direction}...`);
    
    const result = await apiRequest('/player/move', 'POST', {
        session_id: gameState.sessionId,
        direction: direction,
        room_positions: gameState.roomPositions,
        room_info: gameState.roomInfo
    });
    
    hideLoading();
    
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
        
        // Initialize allies array if needed
        if (!gameState.player.allies) {
            gameState.player.allies = [];
        }
        
        // Check if recruitment was successful
        if (ally.ally_recruited === false) {
            // Failed to recruit (at capacity or duplicate)
            if (ally.at_capacity) {
                addLogEntry(`🤝 ${ally.message} Your party is full (4/4 allies).`, 'warning');
                addLogEntry(`💡 Open the Allies menu during combat to fire an ally and make room.`, 'info');
            } else {
                addLogEntry(`🤝 ${ally.message}`, 'warning');
            }
        } else {
            // Successfully recruited
            addLogEntry(`🤝 ${ally.message}`, 'success');
            
            // Add the ally to the player's allies array
            if (ally.ally) {
                gameState.player.allies.push(ally.ally);
                
                // Show ally encounter display with sprite
                showAllyEncounter(ally.ally);
            }
        }
        
        updatePlayerDisplay();
        updateAlliesList();
    }
    
    // Handle enemy encounter
    if (result.data.encounter_occurred && result.data.encounter_result) {
        handleEncounter(result.data.encounter_result);
    }
    
    // Check for achievement unlocks
    checkAchievementsUnlocked(result);
}

// Handle encounter
function handleEncounter(encounterData) {
    if (!encounterData || !encounterData.data) return;
    
    const encounter = encounterData.data;
    gameState.inCombat = true;
    gameState.currentEnemy = encounter.enemy;
    gameState.currentAlly = encounter.ally || null;
    
    // Fetch and cache sprite for this enemy
    if (encounter.enemy) {
        fetchEnemySprite(encounter.enemy.name, encounter.enemy.description).then(spritePath => {
            if (spritePath) {
                gameState.enemySprite = spritePath;
                console.log(`Loaded sprite for enemy: ${encounter.enemy.name}`);
            }
        });
    }
    
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
    
    // Display player sprite
    if (gameState.playerSprite && elements.playerSprite) {
        elements.playerSprite.src = gameState.playerSprite;
        elements.playerSpriteContainer.style.display = 'flex';
    }
    
    if (gameState.currentEnemy) {
        elements.enemyName.textContent = gameState.currentEnemy.name || 'Unknown Enemy';
        elements.enemyDescription.textContent = gameState.currentEnemy.description || 'A mysterious creature';
        
        console.log('showCombatArea: currentEnemy =', gameState.currentEnemy);
        console.log('showCombatArea: enemy ailments =', gameState.currentEnemy.ailments);
        console.log('showCombatArea: enemy can inflict =', gameState.currentEnemy.ailment_inflict_types || [gameState.currentEnemy.ailment_inflict_type], gameState.currentEnemy.ailment_inflict_chance);
        
        // Update all ailment displays
        updateAilmentDisplays();
        
        // Display enemy sprite
        if (gameState.enemySprite) {
            console.log(`✓ Displaying enemy sprite: ${gameState.enemySprite}`);
            elements.enemySprite.src = gameState.enemySprite;
            elements.enemySprite.style.display = 'block';
        } else {
            console.log('⟳ No sprite cached, fetching...');
            // Fetch sprite asynchronously (don't await to avoid blocking combat display)
            fetchEnemySprite(gameState.currentEnemy.name, gameState.currentEnemy.description);
        }
        
        const currentHealth = gameState.currentEnemy.health || 0;
        const maxHealth = gameState.currentEnemy.max_health || 1;
        const enemyHealthPercent = (currentHealth / maxHealth) * 100;
        
        elements.enemyHealthBar.style.width = `${enemyHealthPercent}%`;
        elements.enemyHealthText.textContent = `${currentHealth}/${maxHealth}`;
        
        // Get stat ailment indicators for enemy
        const getEnemyStatAilmentIndicator = (ailmentType) => {
            if (!gameState.currentEnemy.ailments) return '';
            for (const ailment of gameState.currentEnemy.ailments) {
                if (ailment.type === ailmentType) {
                    const statEmoji = ailment.type === 'weakened' ? '💔' : 
                                     ailment.type === 'irradiated' ? '☢️' : 
                                     ailment.type === 'shackled' ? '⛓️' : '';
                    return statEmoji ? ` ${statEmoji}` : '';
                }
            }
            return '';
        };
        
        elements.enemyAttack.textContent = (gameState.currentEnemy.attack_power || 0) + getEnemyStatAilmentIndicator('weakened');
        elements.enemyDefense.textContent = (gameState.currentEnemy.defense || 0) + getEnemyStatAilmentIndicator('irradiated');
        elements.enemySpeed.textContent = (gameState.currentEnemy.speed || 10) + getEnemyStatAilmentIndicator('shackled');
        
        // Update enemy element display
        const enemyElementEl = document.getElementById('enemy-element');
        if (enemyElementEl && gameState.currentEnemy.element) {
            const elementEmoji = getElementEmoji(gameState.currentEnemy.element);
            const elementName = formatElementName(gameState.currentEnemy.element);
            enemyElementEl.textContent = `${elementEmoji} ${elementName}`;
            
            // Apply color-coded effectiveness classes using player's attack element
            let badgeClass = 'element-badge element-badge-neutral';
            let titleText = `Department: ${elementName} - Neutral matchup`;
            
            if (gameState.player && gameState.player.attack_element) {
                const advantage = getElementAdvantage(gameState.player.attack_element, gameState.currentEnemy.element);
                if (advantage === 'advantage') {
                    badgeClass = 'element-badge element-badge-effective';
                    titleText = `Department: ${elementName} - You have ADVANTAGE! (1.25x damage)`;
                } else if (advantage === 'disadvantage') {
                    badgeClass = 'element-badge element-badge-weak';
                    titleText = `Department: ${elementName} - You have DISADVANTAGE! (0.8x damage)`;
                }
            }
            
            enemyElementEl.className = badgeClass;
            enemyElementEl.title = titleText;
        }
    }
    
    // Show/hide ally button based on allies array AND if ally hasn't been used this battle
    // Also check if player is infatuated
    const isInfatuated = gameState.player && gameState.player.ailments && 
                        gameState.player.ailments.some(a => a.type === 'infatuated');
    
    if (gameState.player && gameState.player.allies && gameState.player.allies.length > 0 && !gameState.player.ally_used && !isInfatuated) {
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
    console.log('DEBUG hideCombatArea: Hiding combat and resetting state');
    elements.combatArea.classList.add('hidden');
    elements.enemySprite.style.display = 'none';
    elements.enemySprite.src = '';
    gameState.inCombat = false;
    gameState.currentEnemy = null;
    gameState.currentAlly = null;
    gameState.enemySprite = null;
    gameState.enemySprite = null; // Clear the cached sprite for this battle
    
    // Clean up allies with 0 uses remaining
    if (gameState.player && gameState.player.allies) {
        const removedAllies = gameState.player.allies.filter(ally => ally.uses_remaining === 0);
        gameState.player.allies = gameState.player.allies.filter(ally => ally.uses_remaining > 0);
        
        if (removedAllies.length > 0) {
            removedAllies.forEach(ally => {
                addLogEntry(`${ally.name} has left the party (no uses remaining).`, 'info');
            });
        }
    }
    
    updateMovementButtons();
}

// Perform combat action
async function performCombatAction(action, useAlly = false, allyIndex = null, timingMultiplier = null) {
    // Prevent multiple simultaneous attacks
    if (gameState.isLoading) {
        console.warn('Already loading, ignoring duplicate combat action');
        return;
    }
    
    // Set loading state WITHOUT showing overlay for attacks (so we can see the animation)
    gameState.isLoading = true;
    
    // Show combat loading indicator
    if (elements.combatLoadingIndicator) {
        elements.combatLoadingIndicator.classList.remove('hidden');
    }
    
    // Apply random attack animation to player sprite when attacking
    if (action === 'attack' && gameState.inCombat && elements.playerSprite && elements.playerSprite.src) {
        const playerAttackAnimation = selectRandomPlayerAttackAnimation();
        console.log(`🎬 Applying player attack animation: ${playerAttackAnimation}`);
        removeAttackAnimations(); // Clear any previous animation
        elements.playerSprite.classList.add(playerAttackAnimation);
        
        // Remove the animation class after it completes
        setTimeout(() => {
            if (elements.playerSprite) {
                elements.playerSprite.classList.remove(playerAttackAnimation);
            }
        }, 1000); // Matches the longest animation duration
    }
    
    // Apply random attack animation to enemy sprite in combat area (enemy counter-attack)
    if (gameState.inCombat && elements.enemySprite && elements.enemySprite.src) {
        // Delay enemy animation slightly so player attacks first
        setTimeout(() => {
            const attackAnimation = selectRandomAttackAnimation();
            console.log(`🎬 Applying enemy attack animation: ${attackAnimation}`);
            if (elements.enemySprite) {
                elements.enemySprite.classList.add(attackAnimation);
            }
            
            // Remove enemy animation after it completes
            setTimeout(() => {
                if (elements.enemySprite) {
                    elements.enemySprite.classList.remove(attackAnimation);
                }
            }, 1000);
        }, 400); // Enemy attacks after player
    }
    
    try {
        const requestBody = {
            session_id: gameState.sessionId,
            action: action,
            use_ally: useAlly
        };
        
        // Add timing multiplier if provided
        if (timingMultiplier !== null && timingMultiplier !== undefined) {
            requestBody.timing_multiplier = timingMultiplier;
        }
        
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
        
            console.log('DEBUG performCombatAction: Combat result received:', combatData);
            console.log('DEBUG performCombatAction: Battle ended?', combatData.battle_ended);
            console.log('DEBUG performCombatAction: Player in_battle?', combatData.player?.in_battle);
            console.log('DEBUG performCombatAction: Enemy data:', combatData.enemy);
            
            // Add combat messages to log with enhanced animations
            if (combatData.messages) {
                combatData.messages.forEach(msg => {
                    // Check if message is an object with a description field
                    const messageText = typeof msg === 'object' && msg.description ? msg.description : msg;
                    
                    // Check for critical hits or special messages
                    if (messageText.toLowerCase().includes('critical') || messageText.toLowerCase().includes('devastating')) {
                        animateCriticalHit(messageText);
                        // Create particle effect at center of screen
                        const centerX = window.innerWidth / 2;
                        const centerY = window.innerHeight / 2;
                        createParticles(centerX, centerY, '#ff0000', 20);
                        shakeElement(document.querySelector('.combat-area'));
                    } else {
                        addLogEntry(messageText, 'important');
                    }
                });
            }
            
            // Update player state
            if (combatData.player) {
                console.log('DEBUG performCombatAction: Updating player state');
                console.log('DEBUG performCombatAction: Received player data with allies:', combatData.player.allies);
                console.log('DEBUG performCombatAction: Received player health:', combatData.player.health);
                
                // Parse health if it's a string like "50/100"
                if (typeof combatData.player.health === 'string' && combatData.player.health.includes('/')) {
                    const [current, max] = combatData.player.health.split('/').map(Number);
                    gameState.player.health = current;
                    gameState.player.max_health = max;
                } else {
                    gameState.player.health = combatData.player.health;
                }
                
                gameState.player.gold = combatData.player.gold;
                gameState.player.level = combatData.player.level;
                gameState.player.in_battle = combatData.player.in_battle;
                gameState.player.allies = combatData.player.allies || [];
                gameState.player.ally_used = combatData.player.ally_used || false;
                gameState.player.ailments = combatData.player.ailments || [];
                console.log('DEBUG performCombatAction: Set gameState.player.allies to:', gameState.player.allies);
                console.log('DEBUG performCombatAction: Set gameState.player.ailments to:', gameState.player.ailments);
                updatePlayerDisplay();
                updateAlliesList();
            }
            
            // Update enemy state and animate - ONLY if battle is still ongoing
            if (combatData.enemy && gameState.inCombat && !combatData.battle_ended && combatData.player?.in_battle) {
                console.log('DEBUG performCombatAction: Updating enemy state - battle continues');
                gameState.currentEnemy = combatData.enemy;
                
                // Explicitly update ailment displays
                updateAilmentDisplays();
                
                // Animate enemy taking damage
                const enemyCard = document.querySelector('.enemy-card');
                if (enemyCard && action === 'attack') {
                    shakeElement(enemyCard);
                    animateDamage(enemyCard);
                }
                
                showCombatArea();
            } else {
                console.log('DEBUG performCombatAction: NOT updating enemy state - battle may be ending');
            }
            
            // Check if battle ended - be explicit about checking both conditions
            const battleEnded = combatData.battle_ended === true || combatData.player?.in_battle === false;
            console.log('DEBUG performCombatAction: Battle ended check -', {
                battle_ended: combatData.battle_ended,
                player_in_battle: combatData.player?.in_battle,
                calculated_battleEnded: battleEnded
            });
            
            if (battleEnded) {
                console.log('DEBUG performCombatAction: Battle is ending');
                if (combatData.victory) {
                    addLogEntry(`🎉 Victory! Gained ${combatData.gold_reward || 0} gold and ${combatData.exp_reward || 0} XP!`, 'success');
                    
                    // Check for achievement unlocks
                    checkAchievementsUnlocked(result);
                    
                    // Victory particles
                    const combatArea = document.querySelector('.combat-area');
                    if (combatArea) {
                        const rect = combatArea.getBoundingClientRect();
                        createParticles(rect.left + rect.width / 2, rect.top + rect.height / 2, '#2ecc71', 25);
                    }
                    
                    pulseElement(document.querySelector('.player-stats'));
                } else if (combatData.fled) {
                    addLogEntry(`🏃 Successfully fled from battle!`, 'success');
                }
                
                console.log('DEBUG performCombatAction: Calling hideCombatArea()');
                hideCombatArea();
            } else {
                console.log('DEBUG performCombatAction: Battle continues, not hiding combat area');
            }
            
            // Check if player died
            if (combatData.player && !combatData.player.is_alive) {
                // Pass the death message if available
                const deathMessage = result.message || combatData.message || null;
                handlePlayerDeath(deathMessage);
            }
        }
    } catch (error) {
        console.error('ERROR in performCombatAction:', error);
        addLogEntry(`Combat error: ${error.message}`, 'danger');
    } finally {
        // Clear loading state and remove attack animation
        gameState.isLoading = false;
        removeAttackAnimations();
        
        // Hide combat loading indicator
        if (elements.combatLoadingIndicator) {
            elements.combatLoadingIndicator.classList.add('hidden');
        }
    }
}

// Handle player death
function handlePlayerDeath(deathMessage = null) {
    addLogEntry('💀 You have fallen in battle...', 'danger');
    
    // Store death message for the game over screen
    if (deathMessage) {
        gameState.deathMessage = deathMessage;
    }
    
    setTimeout(() => {
        elements.finalGold.textContent = gameState.player.gold;
        elements.finalLevel.textContent = gameState.player.level || 1;
        elements.finalFloor.textContent = gameState.player.floor;
        elements.finalAllies.textContent = gameState.player.allies_count || 0;
        
        // Display death message if available
        if (elements.deathMessage) {
            elements.deathMessage.textContent = gameState.deathMessage || 
                `You were slain on floor ${gameState.player.floor}...`;
        }
        
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
        const basic = stats.basic_stats || {};
        const progress = stats.progress_stats || {};
        const calculated = stats.calculated_stats || {};
        
        elements.modalStatsContent.innerHTML = `
            <div class="stat-category">
                <h3>Character Stats</h3>
                <div class="stat-row">
                    <span class="stat-label">Name:</span>
                    <span class="stat-value">${basic.name || gameState.player?.name || 'Unknown'}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Level:</span>
                    <span class="stat-value">${gameState.player?.level || 1}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Experience:</span>
                    <span class="stat-value">${gameState.player?.experience || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Health:</span>
                    <span class="stat-value">${basic.health || '0/0'}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Attack Power:</span>
                    <span class="stat-value">${basic.attack_power || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Defense:</span>
                    <span class="stat-value">${basic.defense || 0}</span>
                </div>
            </div>
            <div class="stat-category">
                <h3>Progress</h3>
                <div class="stat-row">
                    <span class="stat-label">Current Floor:</span>
                    <span class="stat-value">${basic.current_floor || 1}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Gold:</span>
                    <span class="stat-value">${basic.current_gold || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Allies:</span>
                    <span class="stat-value">${progress.allies_found || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Rooms Visited:</span>
                    <span class="stat-value">${progress.rooms_visited || 0}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Survival Score:</span>
                    <span class="stat-value">${calculated.survival_score || 0}</span>
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
        const rank = entry.rank || (index + 1);
        const rankClass = rank <= 3 ? `rank-${rank}` : '';
        
        return `
            <div class="leaderboard-entry ${rankClass}">
                <div class="leaderboard-rank">#${rank}</div>
                <div class="leaderboard-info">
                    <div class="leaderboard-name">${entry.name || 'Anonymous'}</div>
                    <div class="leaderboard-details">Floor ${entry.floor || 1} • Level ${entry.level || 1}</div>
                </div>
                <div class="leaderboard-score">${entry.gold || 0} 💰</div>
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
    
    // Prevent multiple simultaneous purchases
    if (!showLoading('Purchasing...')) {
        return;
    }
    
    addLogEntry(`Purchasing ${itemName}...`, 'info');
    
    const result = await apiRequest('/shop/purchase', 'POST', {
        session_id: gameState.sessionId,
        item_name: itemName
    });
    
    hideLoading();
    
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
    
    // Check for achievement unlocks
    checkAchievementsUnlocked(result);
    
    // Animate gold change
    animateGoldChange(elements.playerGold);
    
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
    
    // Store casino data
    gameState.casinoGames = result.data.games || [];
    
    // Update player gold display in casino
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    
    // Show game selection menu
    showCasinoGameMenu();
    
    // Show casino modal
    elements.casinoModal.classList.add('active');
}

// Show casino game selection menu
function showCasinoGameMenu() {
    // Hide all screens
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    const slotsGame = document.getElementById('casino-slots-game');
    if (slotsGame) slotsGame.classList.add('hidden');
    const rouletteGame = document.getElementById('casino-roulette-game');
    if (rouletteGame) rouletteGame.classList.add('hidden');
    
    // Show game menu
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) {
        gameMenu.classList.remove('hidden');
        
        // Populate game options
        const gameList = document.getElementById('casino-game-list');
        if (gameList && gameState.casinoGames) {
            gameList.innerHTML = gameState.casinoGames.map(game => `
                <button class="casino-game-option" onclick="selectCasinoGame('${game.id}')">
                    <div class="game-name">${game.name}</div>
                    <div class="game-description">${game.description}</div>
                </button>
            `).join('');
        }
    }
}

// Select a casino game
function selectCasinoGame(gameId) {
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) {
        gameMenu.classList.add('hidden');
    }
    
    // Store selected game
    gameState.selectedCasinoGame = gameId;
    
    // Show appropriate screen based on game
    if (gameId === 'blackjack') {
        elements.casinoBetScreen.classList.remove('hidden');
    } else if (gameId === 'slots') {
        showSlotsGame();
    } else if (gameId === 'roulette') {
        showRouletteGame();
    } else if (gameId === 'pachinko') {
        showPachinkoGame();
    } else if (gameId === 'dice') {
        showDiceGame();
    }
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

// Split in blackjack
async function blackjackSplit() {
    const result = await apiRequest('/casino/blackjack/split', 'POST', {
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
        addLogEntry(result.data.game.message, 'info');
    }
}

// Double down in blackjack
async function blackjackDouble() {
    const result = await apiRequest('/casino/blackjack/double', 'POST', {
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
    
    // Display player main hand
    let playerHandHTML = '<div class="hand-container">';
    if (game.is_split) {
        playerHandHTML += `<div class="split-hand ${game.active_hand === 'main' ? 'active-hand' : ''}">`;
        playerHandHTML += '<span class="hand-label">Main Hand</span>';
    }
    playerHandHTML += game.player_cards.map(card => 
        `<span class="playing-card">${card}</span>`
    ).join(' ');
    if (game.is_split) {
        playerHandHTML += `<span class="hand-value">${game.player_value}</span></div>`;
    }
    
    // Display split hand if applicable
    if (game.is_split && game.split_cards) {
        playerHandHTML += `<div class="split-hand ${game.active_hand === 'split' ? 'active-hand' : ''}">`;
        playerHandHTML += '<span class="hand-label">Split Hand</span>';
        playerHandHTML += game.split_cards.map(card => 
            `<span class="playing-card">${card}</span>`
        ).join(' ');
        playerHandHTML += `<span class="hand-value">${game.split_value}</span></div>`;
    }
    playerHandHTML += '</div>';
    
    elements.playerCards.innerHTML = playerHandHTML;
    
    // Update player value display (show main hand value if not split)
    if (!game.is_split) {
        elements.playerValue.textContent = game.player_value;
    } else {
        elements.playerValue.textContent = `Playing: ${game.active_hand}`;
    }
    
    // Show/hide controls based on game state
    if (game.game_over) {
        elements.hitBtn.classList.add('hidden');
        elements.standBtn.classList.add('hidden');
        elements.splitBtn.classList.add('hidden');
        elements.doubleBtn.classList.add('hidden');
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
        
        // Show/hide split and double buttons based on availability
        if (game.can_split) {
            elements.splitBtn.classList.remove('hidden');
        } else {
            elements.splitBtn.classList.add('hidden');
        }
        
        if (game.can_double) {
            elements.doubleBtn.classList.remove('hidden');
        } else {
            elements.doubleBtn.classList.add('hidden');
        }
        
        // Display current message if any
        if (game.message) {
            elements.gameMessage.textContent = game.message;
            elements.gameMessage.className = 'game-message info';
        } else {
            elements.gameMessage.textContent = '';
        }
    }
}

// ============================================
// SLOTS GAME FUNCTIONS
// ============================================

function showSlotsGame() {
    // Hide all other screens
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) gameMenu.classList.add('hidden');
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    const rouletteGame = document.getElementById('casino-roulette-game');
    if (rouletteGame) rouletteGame.classList.add('hidden');
    const pachinkoGame = document.getElementById('casino-pachinko-game');
    if (pachinkoGame) pachinkoGame.classList.add('hidden');
    const diceGame = document.getElementById('casino-dice-game');
    if (diceGame) diceGame.classList.add('hidden');
    
    // Show slots screen
    const slotsContainer = document.getElementById('casino-slots-game');
    if (slotsContainer) {
        slotsContainer.classList.remove('hidden');
        // Clear previous results
        const resultDisplay = document.getElementById('slots-result');
        if (resultDisplay) resultDisplay.innerHTML = '';
    }
}

async function spinSlots() {
    const betInput = document.getElementById('slots-bet');
    const bet = parseInt(betInput.value);
    
    if (!bet || bet <= 0) {
        addLogEntry('Please enter a valid bet amount', 'danger');
        return;
    }
    
    if (bet > gameState.player.gold) {
        addLogEntry(`Not enough gold! You have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    // Disable button during spin
    const spinBtn = document.getElementById('spin-slots-btn');
    if (spinBtn) spinBtn.disabled = true;
    
    // Add spinning animation
    const reelsDisplay = document.getElementById('slots-reels');
    if (reelsDisplay) {
        reelsDisplay.classList.add('spinning');
        reelsDisplay.textContent = '🎰 🎰 🎰';
    }
    
    // Wait a bit for animation
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const result = await apiRequest('/casino/slots/spin', 'POST', {
        session_id: gameState.sessionId,
        bet: bet
    });
    
    if (result.error) {
        addLogEntry(`Slots error: ${result.message}`, 'danger');
        if (spinBtn) spinBtn.disabled = false;
        if (reelsDisplay) reelsDisplay.classList.remove('spinning');
        return;
    }
    
    // Display reels
    if (reelsDisplay) {
        reelsDisplay.classList.remove('spinning');
        reelsDisplay.textContent = result.data.reels.join(' ');
    }
    
    // Display result
    const resultDisplay = document.getElementById('slots-result');
    const netGain = result.data.net_gain;
    if (resultDisplay) {
        const color = netGain > 0 ? 'success' : netGain < 0 ? 'danger' : 'info';
        resultDisplay.innerHTML = `
            <div class="${color}">${result.message}</div>
            <div>Bet: ${result.data.bet} | Won: ${result.data.winnings}</div>
            <div>Net: ${netGain >= 0 ? '+' : ''}${netGain}</div>
        `;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    updatePlayerDisplay();
    
    addLogEntry(result.message, netGain > 0 ? 'success' : 'info');
    
    // Check for achievement unlocks
    checkAchievementsUnlocked(result);
    
    // Re-enable button
    if (spinBtn) {
        spinBtn.disabled = false;
        console.log('Slots spin button re-enabled');
    }
}

// ============================================
// ROULETTE GAME FUNCTIONS
// ============================================

function showRouletteGame() {
    // Hide all other screens
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) gameMenu.classList.add('hidden');
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    const slotsGame = document.getElementById('casino-slots-game');
    if (slotsGame) slotsGame.classList.add('hidden');
    const pachinkoGame = document.getElementById('casino-pachinko-game');
    if (pachinkoGame) pachinkoGame.classList.add('hidden');
    const diceGame = document.getElementById('casino-dice-game');
    if (diceGame) diceGame.classList.add('hidden');
    
    // Show roulette screen
    const rouletteContainer = document.getElementById('casino-roulette-game');
    if (rouletteContainer) {
        rouletteContainer.classList.remove('hidden');
        // Clear previous results
        const resultDisplay = document.getElementById('roulette-result');
        if (resultDisplay) resultDisplay.innerHTML = '';
    }
}

async function spinRoulette() {
    const betInput = document.getElementById('roulette-bet');
    const betType = document.getElementById('roulette-bet-type').value;
    const numberInput = document.getElementById('roulette-number');
    const bet = parseInt(betInput.value);
    
    if (!bet || bet <= 0) {
        addLogEntry('Please enter a valid bet amount', 'danger');
        return;
    }
    
    if (bet > gameState.player.gold) {
        addLogEntry(`Not enough gold! You have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    const requestData = {
        session_id: gameState.sessionId,
        bet: bet,
        bet_type: betType
    };
    
    if (betType === 'number') {
        const number = parseInt(numberInput.value);
        if (isNaN(number) || number < 0 || number > 36) {
            addLogEntry('Please enter a number between 0-36', 'danger');
            return;
        }
        requestData.number = number;
    }
    
    // Disable button during spin
    const spinBtn = document.getElementById('spin-roulette-btn');
    if (spinBtn) spinBtn.disabled = true;
    
    // Show spinning animation
    const resultDisplay = document.getElementById('roulette-result');
    if (resultDisplay) {
        resultDisplay.innerHTML = '<div class="roulette-wheel spinning">🎡 Spinning... 🎡</div>';
    }
    
    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const result = await apiRequest('/casino/roulette/spin', 'POST', requestData);
    
    if (result.error) {
        addLogEntry(`Roulette error: ${result.message}`, 'danger');
        if (spinBtn) spinBtn.disabled = false;
        if (resultDisplay) resultDisplay.innerHTML = '';
        return;
    }
    
    // Display result
    const netGain = result.data.net_gain;
    if (resultDisplay) {
        const color = netGain > 0 ? 'success' : netGain < 0 ? 'danger' : 'info';
        const colorEmoji = result.data.color === 'red' ? '❤️' : result.data.color === 'black' ? '🖤' : '💚';
        resultDisplay.innerHTML = `
            <div class="roulette-wheel">${colorEmoji} ${result.data.result} ${colorEmoji}</div>
            <div class="${color}">${result.message}</div>
            <div>Bet: ${result.data.bet} (${result.data.bet_type}) | Won: ${result.data.winnings}</div>
            <div>Net: ${netGain >= 0 ? '+' : ''}${netGain}</div>
        `;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    updatePlayerDisplay();
    
    addLogEntry(result.message, netGain > 0 ? 'success' : 'info');
    
    // Re-enable button
    if (spinBtn) {
        spinBtn.disabled = false;
        console.log('Roulette spin button re-enabled');
    }
}

function updateRouletteNumberInput() {
    const betType = document.getElementById('roulette-bet-type').value;
    const numberInput = document.getElementById('roulette-number');
    const numberGroup = document.getElementById('roulette-number-group');
    
    if (betType === 'number') {
        numberGroup.classList.remove('hidden');
    } else {
        numberGroup.classList.add('hidden');
    }
}

// ============================================
// PACHINKO GAME FUNCTIONS
// ============================================

function showPachinkoGame() {
    // Hide all other screens
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) gameMenu.classList.add('hidden');
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    const slotsGame = document.getElementById('casino-slots-game');
    if (slotsGame) slotsGame.classList.add('hidden');
    const rouletteGame = document.getElementById('casino-roulette-game');
    if (rouletteGame) rouletteGame.classList.add('hidden');
    const diceGame = document.getElementById('casino-dice-game');
    if (diceGame) diceGame.classList.add('hidden');
    
    // Show pachinko screen
    const pachinkoContainer = document.getElementById('casino-pachinko-game');
    if (pachinkoContainer) {
        pachinkoContainer.classList.remove('hidden');
        // Clear previous results
        const resultDisplay = document.getElementById('pachinko-result');
        if (resultDisplay) resultDisplay.innerHTML = '';
    }
}

async function dropBalls() {
    const ballsInput = document.getElementById('pachinko-balls');
    const balls = parseInt(ballsInput.value);
    
    if (!balls || balls <= 0) {
        addLogEntry('Please enter a valid number of balls', 'danger');
        return;
    }
    
    if (balls > 50) {
        addLogEntry('Maximum 50 balls at once', 'danger');
        return;
    }
    
    if (balls > gameState.player.gold) {
        addLogEntry(`Not enough gold! You have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    // Disable button during play
    const dropBtn = document.getElementById('drop-balls-btn');
    if (dropBtn) dropBtn.disabled = true;
    
    // Add dropping animation
    const pachinkoDisplay = document.getElementById('pachinko-display');
    if (pachinkoDisplay) {
        pachinkoDisplay.classList.add('dropping');
        pachinkoDisplay.textContent = '🎪 Dropping balls... 🎪';
    }
    
    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const result = await apiRequest('/casino/pachinko/play', 'POST', {
        session_id: gameState.sessionId,
        bet: balls
    });
    
    if (result.error) {
        addLogEntry(`Pachinko error: ${result.message}`, 'danger');
        if (dropBtn) dropBtn.disabled = false;
        if (pachinkoDisplay) {
            pachinkoDisplay.classList.remove('dropping');
            pachinkoDisplay.textContent = '💰 🎰 💎 ⭐ 🎪';
        }
        return;
    }
    
    // Remove animation
    if (pachinkoDisplay) {
        pachinkoDisplay.classList.remove('dropping');
        pachinkoDisplay.textContent = '💰 🎰 💎 ⭐ 🎪';
    }
    
    // Display results
    const resultDisplay = document.getElementById('pachinko-result');
    const netGain = result.data.net_gain;
    if (resultDisplay) {
        const color = netGain > 0 ? 'success' : netGain < 0 ? 'danger' : 'info';
        
        // Count multipliers
        const counts = {};
        result.data.results.forEach(mult => {
            counts[mult] = (counts[mult] || 0) + 1;
        });
        
        const breakdown = Object.keys(counts).sort((a, b) => b - a).map(mult => 
            `${mult}x: ${counts[mult]} balls`
        ).join(', ');
        
        resultDisplay.innerHTML = `
            <div class="${color}">${result.message}</div>
            <div>Balls dropped: ${result.data.balls} | Won: ${result.data.winnings} gold</div>
            <div>Net: ${netGain >= 0 ? '+' : ''}${netGain} gold</div>
            <div style="font-size: 0.9em; margin-top: 5px;">${breakdown}</div>
        `;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    updatePlayerDisplay();
    
    addLogEntry(result.message, netGain > 0 ? 'success' : 'info');
    
    // Re-enable button
    if (dropBtn) {
        dropBtn.disabled = false;
        console.log('Pachinko drop button re-enabled');
    }
}

// ============================================
// DICE GAME FUNCTIONS
// ============================================

function showDiceGame() {
    // Hide all other screens
    const gameMenu = document.getElementById('casino-game-menu');
    if (gameMenu) gameMenu.classList.add('hidden');
    elements.casinoBetScreen.classList.add('hidden');
    elements.casinoGameScreen.classList.add('hidden');
    const slotsGame = document.getElementById('casino-slots-game');
    if (slotsGame) slotsGame.classList.add('hidden');
    const rouletteGame = document.getElementById('casino-roulette-game');
    if (rouletteGame) rouletteGame.classList.add('hidden');
    const pachinkoGame = document.getElementById('casino-pachinko-game');
    if (pachinkoGame) pachinkoGame.classList.add('hidden');
    
    // Show dice screen
    const diceContainer = document.getElementById('casino-dice-game');
    if (diceContainer) {
        diceContainer.classList.remove('hidden');
        // Clear previous results
        const resultDisplay = document.getElementById('dice-result');
        if (resultDisplay) resultDisplay.innerHTML = '';
    }
}

async function rollDiceGame() {
    const betInput = document.getElementById('dice-bet');
    const predictionType = document.getElementById('dice-prediction').value;
    const numberInput = document.getElementById('dice-number');
    const bet = parseInt(betInput.value);
    
    if (!bet || bet <= 0) {
        addLogEntry('Please enter a valid bet amount', 'danger');
        return;
    }
    
    if (bet > gameState.player.gold) {
        addLogEntry(`Not enough gold! You have ${gameState.player.gold}`, 'danger');
        return;
    }
    
    let prediction = predictionType;
    if (predictionType === 'number') {
        const number = parseInt(numberInput.value);
        if (isNaN(number) || number < 2 || number > 12) {
            addLogEntry('Please enter a number between 2-12', 'danger');
            return;
        }
        prediction = number.toString();
    }
    
    // Disable button during roll
    const rollBtn = document.getElementById('roll-dice-btn');
    if (rollBtn) rollBtn.disabled = true;
    
    // Add rolling animation
    const diceDisplay = document.getElementById('dice-display');
    if (diceDisplay) {
        diceDisplay.classList.add('rolling');
        diceDisplay.textContent = '🎲 Rolling... 🎲';
    }
    
    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 600));
    
    const result = await apiRequest('/casino/dice/roll', 'POST', {
        session_id: gameState.sessionId,
        bet: bet,
        prediction: prediction
    });
    
    if (result.error) {
        addLogEntry(`Dice error: ${result.message}`, 'danger');
        if (rollBtn) rollBtn.disabled = false;
        if (diceDisplay) {
            diceDisplay.classList.remove('rolling');
            diceDisplay.textContent = '🎲 ? + ? = ? 🎲';
        }
        return;
    }
    
    // Update display with result
    if (diceDisplay) {
        diceDisplay.classList.remove('rolling');
        diceDisplay.textContent = `🎲 ${result.data.die1} + ${result.data.die2} = ${result.data.total} 🎲`;
    }
    
    // Display result
    const resultDisplay = document.getElementById('dice-result');
    const netGain = result.data.net_gain;
    if (resultDisplay) {
        const color = netGain > 0 ? 'success' : netGain < 0 ? 'danger' : 'info';
        resultDisplay.innerHTML = `
            <div class="${color}">${result.message}</div>
            <div>Bet: ${result.data.bet} on ${result.data.prediction} | Won: ${result.data.winnings}</div>
            <div>Net: ${netGain >= 0 ? '+' : ''}${netGain}</div>
        `;
    }
    
    // Update gold
    gameState.player.gold = result.data.player_gold;
    elements.casinoPlayerGold.textContent = result.data.player_gold;
    updatePlayerDisplay();
    
    addLogEntry(result.message, netGain > 0 ? 'success' : 'info');
    
    // Re-enable button
    if (rollBtn) {
        rollBtn.disabled = false;
        console.log('Dice roll button re-enabled');
    }
}

function updateDiceNumberInput() {
    const predictionType = document.getElementById('dice-prediction').value;
    const numberInput = document.getElementById('dice-number');
    const numberGroup = document.getElementById('dice-number-group');
    
    if (predictionType === 'number') {
        numberGroup.classList.remove('hidden');
    } else {
        numberGroup.classList.add('hidden');
    }
}

// ============================================
// ANIMATION HELPER FUNCTIONS
// ============================================

/**
 * Animate damage taken
 */
function animateDamage(element) {
    if (!element) return;
    element.classList.add('damage-flash');
    setTimeout(() => element.classList.remove('damage-flash'), 500);
}

/**
 * Animate healing
 */
function animateHealing(element) {
    if (!element) return;
    element.classList.add('heal-flash');
    setTimeout(() => element.classList.remove('heal-flash'), 500);
}

/**
 * Animate gold change
 */
function animateGoldChange(element) {
    if (!element) return;
    element.classList.add('updated');
    setTimeout(() => element.classList.remove('updated'), 500);
}

/**
 * Animate level up
 */
function animateLevelUp(element) {
    if (!element) return;
    element.classList.add('level-up');
    setTimeout(() => element.classList.remove('level-up'), 800);
}

/**
 * Animate critical hit
 */
function animateCriticalHit(message) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry critical-hit danger';
    logEntry.textContent = `💥 CRITICAL HIT! ${message}`;
    
    const gameLog = elements.eventLog;
    if (gameLog) {
        gameLog.appendChild(logEntry);
        gameLog.scrollTop = gameLog.scrollHeight;
    }
    
    return logEntry;
}

/**
 * Create floating damage number
 */
function createFloatingNumber(value, x, y, isHealing = false) {
    const floater = document.createElement('div');
    floater.className = `floating-number ${isHealing ? 'healing' : 'damage'}`;
    floater.textContent = isHealing ? `+${value}` : `-${value}`;
    floater.style.position = 'fixed';
    floater.style.left = `${x}px`;
    floater.style.top = `${y}px`;
    floater.style.fontSize = '2rem';
    floater.style.fontWeight = 'bold';
    floater.style.color = isHealing ? '#2ecc71' : '#e74c3c';
    floater.style.textShadow = '0 0 10px currentColor';
    floater.style.pointerEvents = 'none';
    floater.style.zIndex = '9999';
    floater.style.animation = 'floatUp 1s ease-out forwards';
    
    document.body.appendChild(floater);
    
    setTimeout(() => floater.remove(), 1000);
}

/**
 * Add floating number animation CSS
 */
if (!document.getElementById('floating-number-style')) {
    const style = document.createElement('style');
    style.id = 'floating-number-style';
    style.textContent = `
        @keyframes floatUp {
            0% {
                opacity: 1;
                transform: translateY(0);
            }
            100% {
                opacity: 0;
                transform: translateY(-50px);
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Shake an element
 */
function shakeElement(element) {
    if (!element) return;
    element.style.animation = 'shake 0.5s ease-in-out';
    setTimeout(() => element.style.animation = '', 500);
}

/**
 * Pulse an element
 */
function pulseElement(element) {
    if (!element) return;
    element.style.animation = 'pulse 0.6s ease-in-out';
    setTimeout(() => element.style.animation = '', 600);
}

/**
 * Add bounce animation to button click
 */
function bounceButton(button) {
    if (!button) return;
    button.style.animation = 'bounce 0.5s ease-in-out';
    setTimeout(() => button.style.animation = '', 500);
}

/**
 * Create particle effect
 */
function createParticles(x, y, color = '#4a90e2', count = 10) {
    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'fixed';
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        particle.style.width = '8px';
        particle.style.height = '8px';
        particle.style.backgroundColor = color;
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        particle.style.zIndex = '9999';
        
        const angle = (Math.PI * 2 * i) / count;
        const velocity = 2 + Math.random() * 3;
        const tx = Math.cos(angle) * velocity * 50;
        const ty = Math.sin(angle) * velocity * 50;
        
        particle.style.animation = `particleExplosion 0.8s ease-out forwards`;
        particle.style.setProperty('--tx', `${tx}px`);
        particle.style.setProperty('--ty', `${ty}px`);
        
        document.body.appendChild(particle);
        setTimeout(() => particle.remove(), 800);
    }
}

/**
 * Add particle animation CSS
 */
if (!document.getElementById('particle-style')) {
    const style = document.createElement('style');
    style.id = 'particle-style';
    style.textContent = `
        @keyframes particleExplosion {
            0% {
                opacity: 1;
                transform: translate(0, 0) scale(1);
            }
            100% {
                opacity: 0;
                transform: translate(var(--tx), var(--ty)) scale(0);
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Screen transition effect
 */
function transitionScreen(fromScreen, toScreen) {
    fromScreen.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => {
        fromScreen.classList.remove('active');
        fromScreen.style.animation = '';
        toScreen.classList.add('active');
        toScreen.style.animation = 'fadeIn 0.3s ease-in';
        setTimeout(() => toScreen.style.animation = '', 300);
    }, 300);
}

/**
 * Add fade out animation
 */
if (!document.getElementById('fade-out-style')) {
    const style = document.createElement('style');
    style.id = 'fade-out-style';
    style.textContent = `
        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(10px);
            }
        }
    `;
    document.head.appendChild(style);
}

// ============================================
// GEAR EQUIPMENT SYSTEM
// ============================================

/**
 * Open the gear equipment modal
 */
function openGearModal() {
    const modal = document.getElementById('gear-modal');
    if (!modal) return;
    
    updateGearDisplay();
    modal.classList.add('active');
}

/**
 * Update the gear display in the modal
 */
function updateGearDisplay() {
    if (!gameState.player) return;
    
    // Update equipped gear slots
    updateEquippedGearSlot('weapon', gameState.player.equipped_weapon);
    updateEquippedGearSlot('armor', gameState.player.equipped_armor);
    updateEquippedGearSlot('accessory', gameState.player.equipped_accessory);
    
    // Update gear inventory list
    updateGearInventory();
}

/**
 * Update a single equipped gear slot
 */
function updateEquippedGearSlot(slotType, gear) {
    const slotContent = document.getElementById(`${slotType}-slot-content`);
    const unequipBtn = document.getElementById(`unequip-${slotType}-btn`);
    
    if (!slotContent || !unequipBtn) return;
    
    if (gear) {
        slotContent.innerHTML = createGearHTML(gear);
        unequipBtn.style.display = 'block';
    } else {
        slotContent.innerHTML = `<p class="empty-slot">No ${slotType} equipped</p>`;
        unequipBtn.style.display = 'none';
    }
}

/**
 * Create HTML for displaying gear info
 */
function createGearHTML(gear) {
    const rarityClass = gear.rarity || 'common';
    const elementEmoji = gear.element ? getElementEmoji(gear.element) : '';
    const elementName = gear.element ? formatElementName(gear.element) : '';
    
    let statsHTML = '<div class="gear-stats">';
    
    if (gear.attack_bonus && gear.attack_bonus > 0) {
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">⚔️ Attack:</span><span class="gear-stat-value">+${gear.attack_bonus}</span></div>`;
    }
    if (gear.defense_bonus && gear.defense_bonus > 0) {
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">🛡️ Defense:</span><span class="gear-stat-value">+${gear.defense_bonus}</span></div>`;
    }
    if (gear.speed_bonus) {
        const speedSign = gear.speed_bonus > 0 ? '+' : '';
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">⚡ Speed:</span><span class="gear-stat-value">${speedSign}${gear.speed_bonus}</span></div>`;
    }
    
    if (gear.element) {
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">🌟 Element:</span><span class="gear-stat-value">${elementEmoji} ${elementName}</span></div>`;
    }
    
    if (gear.ailment && gear.ailment_chance) {
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">💀 Ailment:</span><span class="gear-stat-value">${gear.ailment} (${Math.round(gear.ailment_chance * 100)}%)</span></div>`;
    }
    
    if (gear.weight) {
        statsHTML += `<div class="gear-stat"><span class="gear-stat-label">⚖️ Weight:</span><span class="gear-stat-value">${gear.weight}</span></div>`;
    }
    
    statsHTML += '</div>';
    
    return `
        <div class="gear-info">
            <div class="gear-name">
                <span>${gear.name}</span>
                <span class="gear-rarity ${rarityClass}">${rarityClass}</span>
            </div>
            ${statsHTML}
        </div>
    `;
}

/**
 * Update the gear inventory list
 */
function updateGearInventory() {
    const inventoryList = document.getElementById('gear-inventory-list');
    if (!inventoryList) return;
    
    // Filter inventory for gear items (items with gear_type property)
    const gearItems = gameState.player.inventory.filter(item => item.gear_type);
    
    if (gearItems.length === 0) {
        inventoryList.innerHTML = '<p class="empty-state">No gear in inventory</p>';
        return;
    }
    
    inventoryList.innerHTML = gearItems.map(gear => {
        // Create a unique ID for this gear item button
        const gearBtnId = `equip-gear-${gear.name.replace(/\s+/g, '-').toLowerCase()}`;
        
        return `
            <div class="gear-inventory-item">
                <div class="gear-header">
                    ${createGearHTML(gear)}
                </div>
                <div class="gear-actions">
                    <button class="btn btn-primary" id="${gearBtnId}" data-gear-name="${gear.name}">Equip</button>
                </div>
            </div>
        `;
    }).join('');
    
    // Add event listeners to all equip buttons
    gearItems.forEach(gear => {
        const gearBtnId = `equip-gear-${gear.name.replace(/\s+/g, '-').toLowerCase()}`;
        const btn = document.getElementById(gearBtnId);
        if (btn) {
            btn.addEventListener('click', () => equipGearFromInventory(gear.name));
        }
    });
}

/**
 * Equip gear from inventory
 */
async function equipGearFromInventory(gearName) {
    console.log('Attempting to equip gear:', gearName);
    
    try {
        const response = await fetch('/api/equip_gear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: gameState.sessionId,
                gear_name: gearName
            })
        });
        
        const data = await response.json();
        console.log('Equip gear response:', data);
        
        if (!data.error) {
            // Update game state
            gameState.player = data.data.player;
            
            // Update displays
            updatePlayerDisplay();
            updateGearDisplay();
            updateInventoryDisplay();
            
            addLogEntry(data.message || 'Gear equipped successfully!', 'success');
        } else {
            console.error('Failed to equip gear:', data.message);
            addLogEntry(data.message || 'Failed to equip gear', 'error');
        }
    } catch (error) {
        console.error('Error equipping gear:', error);
        addLogEntry('Error equipping gear', 'error');
    }
}

/**
 * Unequip gear
 */
async function unequipGear(slotType) {
    console.log('Attempting to unequip gear:', slotType);
    
    try {
        const response = await fetch('/api/unequip_gear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: gameState.sessionId,
                gear_type: slotType
            })
        });
        
        const data = await response.json();
        console.log('Unequip gear response:', data);
        
        if (!data.error) {
            // Update game state
            gameState.player = data.data.player;
            
            // Update displays
            updatePlayerDisplay();
            updateGearDisplay();
            updateInventoryDisplay();
            
            addLogEntry(data.message || 'Gear unequipped successfully!', 'success');
        } else {
            addLogEntry(data.message || 'Failed to unequip gear', 'error');
        }
    } catch (error) {
        console.error('Error unequipping gear:', error);
        addLogEntry('Error unequipping gear', 'error');
    }
}

// ============================================
// SETTINGS FUNCTIONS
// ============================================

function toggleSettings() {
    const panel = document.getElementById('settings-panel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
}

function toggleParticles() {
    const particles = document.querySelector('.particles');
    const checkbox = document.getElementById('toggle-particles');
    
    if (particles && checkbox) {
        if (checkbox.checked) {
            particles.classList.remove('disabled');
            localStorage.setItem('particles-enabled', 'true');
        } else {
            particles.classList.add('disabled');
            localStorage.setItem('particles-enabled', 'false');
        }
    }
}

function toggleAnimations() {
    const checkbox = document.getElementById('toggle-animations');
    
    if (checkbox) {
        if (checkbox.checked) {
            document.body.classList.remove('no-animations');
            localStorage.setItem('animations-enabled', 'true');
        } else {
            document.body.classList.add('no-animations');
            localStorage.setItem('animations-enabled', 'false');
        }
    }
}

function toggleBackgroundPattern() {
    const checkbox = document.getElementById('toggle-background-pattern');
    
    if (checkbox) {
        if (checkbox.checked) {
            document.body.classList.remove('no-background-pattern');
            localStorage.setItem('background-pattern-enabled', 'true');
        } else {
            document.body.classList.add('no-background-pattern');
            localStorage.setItem('background-pattern-enabled', 'false');
        }
    }
}

// Load settings from localStorage on page load
function loadSettings() {
    const particlesEnabled = localStorage.getItem('particles-enabled');
    const animationsEnabled = localStorage.getItem('animations-enabled');
    const backgroundPatternEnabled = localStorage.getItem('background-pattern-enabled');
    
    // Apply particles setting
    if (particlesEnabled === 'false') {
        const particles = document.querySelector('.particles');
        const checkbox = document.getElementById('toggle-particles');
        if (particles) particles.classList.add('disabled');
        if (checkbox) checkbox.checked = false;
    }
    
    // Apply animations setting
    if (animationsEnabled === 'false') {
        document.body.classList.add('no-animations');
        const checkbox = document.getElementById('toggle-animations');
        if (checkbox) checkbox.checked = false;
    }
    
    // Apply background pattern setting
    if (backgroundPatternEnabled === 'false') {
        document.body.classList.add('no-background-pattern');
        const checkbox = document.getElementById('toggle-background-pattern');
        if (checkbox) checkbox.checked = false;
    }
}

// Load settings when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
});

// ==========================================
// ACHIEVEMENTS SYSTEM
// ==========================================

async function showAchievements() {
    // Check if game is started
    if (!gameState.sessionId) {
        addLogEntry('Please start a game first!', 'warning');
        return;
    }
    
    const panel = document.getElementById('achievements-panel');
    panel.classList.remove('hidden');
    
    // Load achievements data
    try {
        const response = await fetch(`/api/player/achievements?session_id=${gameState.sessionId}`);
        const result = await response.json();
        
        console.log('Achievements response:', result);
        
        if (!result.error && result.data) {
            displayAchievements(result.data);
        } else {
            console.error('Achievement load failed:', result);
            document.getElementById('achievements-list').innerHTML = `<p>Error loading achievements: ${result.message || 'Unknown error'}</p>`;
        }
    } catch (error) {
        console.error('Error fetching achievements:', error);
        document.getElementById('achievements-list').innerHTML = '<p>Error loading achievements</p>';
    }
}

function hideAchievements() {
    const panel = document.getElementById('achievements-panel');
    panel.classList.add('hidden');
}

function displayAchievements(data) {
    const summary = document.getElementById('achievements-summary');
    const list = document.getElementById('achievements-list');
    
    // Update summary
    summary.innerHTML = `
        <p><strong>Unlocked:</strong> ${data.total_unlocked} / ${data.total_achievements}</p>
        <p><strong>Total Rewards Earned:</strong> ${data.total_rewards_earned} 💰</p>
    `;
    
    // Display achievements
    list.innerHTML = '';
    data.achievements.forEach(achievement => {
        const card = document.createElement('div');
        card.className = `achievement-card ${achievement.unlocked ? 'unlocked' : ''}`;
        
        const progressPercent = Math.round(achievement.progress * 100);
        const progressText = achievement.unlocked ? 'Completed!' : `${progressPercent}%`;
        
        let unlockedDateHTML = '';
        if (achievement.unlocked && achievement.unlocked_at) {
            const date = new Date(achievement.unlocked_at);
            unlockedDateHTML = `<p class="achievement-unlocked-date">Unlocked: ${date.toLocaleDateString()}</p>`;
        }
        
        card.innerHTML = `
            <div class="achievement-emoji">${achievement.emoji}</div>
            <div class="achievement-info">
                <div class="achievement-name">${achievement.name}</div>
                <div class="achievement-description">${achievement.description}</div>
                <div class="achievement-reward">Reward: ${achievement.reward} 💰</div>
                ${!achievement.unlocked ? `
                    <div class="achievement-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progressPercent}%">
                                ${progressText}
                            </div>
                        </div>
                    </div>
                ` : unlockedDateHTML}
            </div>
        `;
        
        list.appendChild(card);
    });
}

function showAchievementNotification(achievement) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    notification.innerHTML = `
        <div class="achievement-notification-content">
            <div class="achievement-notification-emoji">${achievement.emoji}</div>
            <div class="achievement-notification-info">
                <div class="achievement-notification-title">Achievement Unlocked!</div>
                <div class="achievement-notification-name">${achievement.name}</div>
                <div class="achievement-notification-reward">+${achievement.reward} 💰</div>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}

// Check for achievements after actions and show notifications
function checkAchievementsUnlocked(response) {
    if (response.data && response.data.achievements_unlocked && response.data.achievements_unlocked.length > 0) {
        response.data.achievements_unlocked.forEach(achievement => {
            showAchievementNotification(achievement);
        });
    }
}

