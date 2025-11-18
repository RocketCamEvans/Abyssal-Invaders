/**
 * Developer Panel - In-page overlay for testing and debugging
 */

const DEV_KEY = 'abyssal_dev_2024';

// Tab switching
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.dev-tab');
    const tabContents = document.querySelectorAll('.dev-tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            document.querySelector(`[data-content="${tabName}"]`).classList.add('active');
        });
    });
    
    // Close button
    const closeBtn = document.getElementById('dev-panel-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('dev-panel').classList.add('hidden');
        });
    }
    
    // Update session status periodically
    updateSessionStatus();
    setInterval(updateSessionStatus, 2000); // Check every 2 seconds
    
    devLog('Developer tools ready', 'success');
});

// Update session status display
function updateSessionStatus() {
    const statusElement = document.getElementById('dev-session-status');
    if (!statusElement) return;
    
    if (window.gameState && window.gameState.sessionId) {
        const shortId = window.gameState.sessionId.substring(0, 8);
        statusElement.textContent = `🟢 Session: ${shortId}...`;
        statusElement.className = 'connected';
    } else {
        statusElement.textContent = '🔴 No session - Start a game first';
        statusElement.className = 'disconnected';
    }
}

// Console logging
function devLog(message, type = 'info') {
    const output = document.getElementById('dev-console-output');
    if (!output) return;
    
    const entry = document.createElement('div');
    entry.className = `dev-log-entry dev-log-${type}`;
    
    const time = new Date().toLocaleTimeString();
    const icon = type === 'success' ? '✓' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
    
    entry.textContent = `[${time}] ${icon} ${message}`;
    output.appendChild(entry);
    output.scrollTop = output.scrollHeight;
}

function devClearConsole() {
    const output = document.getElementById('dev-console-output');
    if (output) {
        output.innerHTML = '';
        devLog('Console cleared', 'info');
    }
}

// API request helper
async function devMakeRequest(endpoint, data = {}) {
    try {
        // Debug logging
        console.log('Dev panel checking gameState:', {
            hasWindow: typeof window !== 'undefined',
            hasGameState: typeof window.gameState !== 'undefined',
            gameState: window.gameState,
            sessionId: window.gameState?.sessionId
        });

        if (!window.gameState || !window.gameState.sessionId) {
            devLog('No active game session', 'error');
            devLog('Please start a new game first', 'warning');
            return null;
        }

        data.session_id = window.gameState.sessionId;
        data.key = DEV_KEY;

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        // Backend returns {error: false, message: "..."} for success
        const isSuccess = response.ok && !result.error;
        
        if (isSuccess) {
            devLog(result.message, 'success');
            
            // Update gameState if player data is returned
            if (result.data && result.data.player && window.gameState) {
                window.gameState.player = result.data.player;
                
                // Sync minimap data from player to gameState
                if (result.data.player.room_positions) {
                    window.gameState.roomPositions = result.data.player.room_positions;
                }
                if (result.data.player.room_info) {
                    window.gameState.roomInfo = result.data.player.room_info;
                }
            }
            
            // Update current room if returned
            if (result.data && result.data.room_info && window.gameState) {
                window.gameState.currentRoom = result.data.room_info;
            }
            
            // Update enemy if returned (for ailments, etc)
            if (result.data && result.data.enemy && window.gameState && window.gameState.currentEnemy) {
                console.log('Dev panel: Updating currentEnemy with new data', result.data.enemy);
                window.gameState.currentEnemy = result.data.enemy;
                // Also update player's stored enemy
                if (window.gameState.player) {
                    window.gameState.player.current_enemy = result.data.enemy;
                }
            }
            
            // Handle battle encounter if spawned (new battle)
            if (result.data && result.data.enemy && window.gameState && !window.gameState.currentEnemy) {
                console.log('Dev panel: Spawning new battle encounter');
                // Trigger the encounter handler like a normal battle
                if (typeof handleEncounter === 'function') {
                    handleEncounter(result);
                }
            }
            
            // Refresh UI without full page reload (same as movement system)
            if (typeof updatePlayerDisplay === 'function') {
                updatePlayerDisplay();
            }
            if (typeof updateInventoryDisplay === 'function') {
                updateInventoryDisplay();
            }
            if (typeof updateRoomDisplay === 'function') {
                updateRoomDisplay();
            }
            if (typeof updateMinimap === 'function') {
                updateMinimap();
            }
            
            // Refresh combat display if enemy was updated or we're in combat
            if (result.data && result.data.enemy && window.gameState && (window.gameState.inCombat || window.gameState.currentEnemy)) {
                console.log('Dev panel: Refreshing combat display');
                if (typeof showCombatArea === 'function') {
                    showCombatArea();
                }
            }
            
            devLog('✓ Display refreshed', 'success');
            
            return result;
        } else {
            devLog(result.message || 'Request failed', 'error');
            return null;
        }
    } catch (error) {
        devLog(`Request failed: ${error.message}`, 'error');
        return null;
    }
}

// Stats functions
async function devApplyStats() {
    const data = {};
    
    const health = document.getElementById('dev-stat-health').value;
    const maxHealth = document.getElementById('dev-stat-max-health').value;
    const gold = document.getElementById('dev-stat-gold').value;
    const attack = document.getElementById('dev-stat-attack').value;
    const defense = document.getElementById('dev-stat-defense').value;
    const speed = document.getElementById('dev-stat-speed').value;
    const floor = document.getElementById('dev-stat-floor').value;

    if (health) data.health = parseInt(health);
    if (maxHealth) data.max_health = parseInt(maxHealth);
    if (gold) data.gold = parseInt(gold);
    if (attack) data.attack_power = parseInt(attack);
    if (defense) data.defense = parseInt(defense);
    if (speed) data.speed = parseInt(speed);

    if (Object.keys(data).length === 0 && !floor) {
        devLog('No stats to modify', 'warning');
        return;
    }

    // Apply stats first
    if (Object.keys(data).length > 0) {
        await devMakeRequest('/dev/modify-stats', data);
    }

    // Change floor if specified - use special handling
    if (floor) {
        const result = await devMakeRequest('/dev/change-floor', { floor: parseInt(floor) });
        
        // Force complete minimap reset for floor changes
        if (result && result.data && window.gameState) {
            // The backend sends fresh minimap data with just the start room
            // Force a complete replacement, not a merge
            if (result.data.player.room_positions) {
                window.gameState.roomPositions = result.data.player.room_positions;
                console.log('Dev Panel: Reset roomPositions to', window.gameState.roomPositions);
            }
            if (result.data.player.room_info) {
                window.gameState.roomInfo = result.data.player.room_info;
                console.log('Dev Panel: Reset roomInfo to', window.gameState.roomInfo);
            }
        }
    }

    // Clear input fields after applying
    document.getElementById('dev-stat-health').value = '';
    document.getElementById('dev-stat-max-health').value = '';
    document.getElementById('dev-stat-gold').value = '';
    document.getElementById('dev-stat-attack').value = '';
    document.getElementById('dev-stat-defense').value = '';
    document.getElementById('dev-stat-speed').value = '';
    document.getElementById('dev-stat-floor').value = '';
}

async function devGetPlayerInfo() {
    const result = await devMakeRequest('/dev/get-player-info', {});

    if (result && result.success && result.data.stats) {
        const stats = result.data.stats;
        devLog('=== Player Stats ===', 'info');
        devLog(`HP: ${stats.health}`, 'info');
        devLog(`Gold: ${stats.gold}`, 'info');
        devLog(`Attack: ${stats.attack}`, 'info');
        devLog(`Defense: ${stats.defense}`, 'info');
        devLog(`Speed: ${stats.speed}`, 'info');
        devLog(`Level: ${stats.level}`, 'info');
        devLog(`Floor: ${stats.floor}`, 'info');
        devLog(`In Battle: ${stats.in_battle ? 'Yes' : 'No'}`, 'info');
        devLog(`Allies: ${stats.allies}`, 'info');
        devLog(`Ailments: ${stats.ailments}`, 'info');
    }
}

// Battle functions
async function devSpawnBattle() {
    const floor = document.getElementById('dev-battle-floor').value;
    const enemyName = document.getElementById('dev-battle-enemy-name').value;
    
    // Collect all checked ailment types
    const ailmentCheckboxes = document.querySelectorAll('.dev-ailment-checkbox:checked');
    const ailmentTypes = Array.from(ailmentCheckboxes).map(cb => cb.value);
    
    const ailmentChance = document.getElementById('dev-battle-ailment-chance').value;
    const ailmentSeverity = document.getElementById('dev-battle-ailment-severity').value;

    const data = {
        floor: parseInt(floor),
        enemy_name: enemyName,
        enemy_description: ''
    };
    
    // Add ailment parameters if any are selected
    if (ailmentTypes.length > 0) {
        data.ailment_types = ailmentTypes;
        data.ailment_chance = parseInt(ailmentChance) / 100; // Convert percentage to decimal
        data.ailment_severity = parseInt(ailmentSeverity);
        console.log('Dev spawn battle: Adding ailments -', ailmentTypes, 'with chance', data.ailment_chance, 'severity', data.ailment_severity);
    }

    console.log('Dev spawn battle request:', data);
    await devMakeRequest('/dev/spawn-battle', data);
}

async function devEndBattle() {
    await devMakeRequest('/dev/end-battle', {});
}

// Room functions
async function devSpawnRoom() {
    const roomType = document.getElementById('dev-room-type').value;
    const floor = document.getElementById('dev-room-floor').value;

    await devMakeRequest('/dev/spawn-room', {
        room_type: roomType,
        floor: parseInt(floor)
    });
}

async function devSpawnCasino() {
    const result = await devMakeRequest('/dev/spawn-casino', {});
    
    // Update gameState with the new room info
    if (result && result.data && result.data.room_info) {
        window.gameState.currentRoom = result.data.room_info;
        
        // Force update the room display
        if (typeof updateRoomDisplay === 'function') {
            updateRoomDisplay();
        }
    }
}

// Ally functions
async function devGiveAlly() {
    const allyName = document.getElementById('dev-ally-name').value;

    await devMakeRequest('/dev/give-ally', {
        ally_name: allyName
    });

    // Clear input after giving
    document.getElementById('dev-ally-name').value = '';
}

async function devListAllies() {
    const result = await devMakeRequest('/dev/list-allies', {});

    if (result && result.success) {
        const listDiv = document.getElementById('dev-allies-list');
        listDiv.innerHTML = '';

        const allies = result.data.available_allies || [];
        const playerAllies = result.data.player_allies || [];

        devLog(`Player has ${playerAllies.length} allies`, 'info');

        if (allies.length > 0) {
            allies.forEach(ally => {
                const item = document.createElement('div');
                item.className = 'dev-ally-item';
                item.innerHTML = `
                    <div class="dev-ally-name">${ally.name}</div>
                    <div class="dev-ally-type">${ally.type} (${ally.value})</div>
                `;
                item.onclick = () => {
                    document.getElementById('dev-ally-name').value = ally.name;
                    devLog(`Selected: ${ally.name}`, 'success');
                };
                listDiv.appendChild(item);
            });
        }
    }
}

// Ailment functions
async function devInflictAilment() {
    const target = document.getElementById('dev-ailment-target').value;
    const type = document.getElementById('dev-ailment-type').value;
    const severity = document.getElementById('dev-ailment-severity').value;

    await devMakeRequest('/dev/inflict-ailment', {
        target: target,
        ailment_type: type,
        severity: parseInt(severity)
    });
}

// Inventory functions
async function devAddItem() {
    const itemType = document.getElementById('dev-item-type').value;
    const quantity = document.getElementById('dev-item-quantity').value;

    const result = await devMakeRequest('/dev/add-item', {
        item_type: itemType,
        quantity: parseInt(quantity)
    });

    if (result && result.success) {
        devLog(`Added ${quantity}x ${itemType} to inventory`, 'success');
    }
}

async function devAddGear() {
    const gearType = document.getElementById('dev-gear-type').value;
    const floor = document.getElementById('dev-gear-floor').value;
    const quantity = document.getElementById('dev-gear-quantity').value;

    const result = await devMakeRequest('/dev/add-gear', {
        gear_type: gearType,
        floor: parseInt(floor),
        quantity: parseInt(quantity)
    });

    if (result && result.success) {
        devLog(`Added ${quantity}x ${gearType} (floor ${floor}) to inventory`, 'success');
    }
}

async function devClearInventory() {
    if (!confirm('Are you sure you want to clear all inventory items?')) {
        return;
    }

    const result = await devMakeRequest('/dev/clear-inventory', {});

    if (result && result.success) {
        devLog('Cleared all inventory items', 'success');
    }
}

async function devShowInventory() {
    if (!window.gameState || !window.gameState.player) {
        devLog('No active game session', 'error');
        return;
    }

    const inventory = window.gameState.player.inventory || [];
    
    devLog('=== INVENTORY ===', 'info');
    devLog(`Total items: ${inventory.length}`, 'info');
    
    if (inventory.length === 0) {
        devLog('Inventory is empty', 'warning');
    } else {
        inventory.forEach((item, index) => {
            if (item.gear_type) {
                // This is gear
                devLog(`${index + 1}. [GEAR] ${item.name} (${item.gear_type}, ${item.rarity})`, 'success');
            } else {
                // This is an item
                devLog(`${index + 1}. [ITEM] ${item.name} (${item.type})`, 'success');
            }
        });
    }
    
    devLog('================', 'info');
}

