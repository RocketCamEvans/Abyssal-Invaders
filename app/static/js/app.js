// Abyssal Invaders Web Client
const API = window.ABYSSAL_API || '/api';
let sessionId = null;
let lastEnemy = null;
let combatLog = [];
let inBattle = false;

const els = {
  playerStats: document.getElementById('player-stats'),
  roomInfo: document.getElementById('room-info'),
  messages: document.getElementById('messages'),
  combatLog: document.getElementById('combat-log'),
  highScores: document.getElementById('high-scores'),
  newPlayerBtn: document.getElementById('btn-new-player'),
  refreshBtn: document.getElementById('btn-refresh'),
  submitScoreBtn: document.getElementById('btn-submit-score'),
  deleteBtn: document.getElementById('btn-delete'),
  attackBtn: document.getElementById('btn-attack'),
  allyBtn: document.getElementById('btn-use-ally'),
  fleeBtn: document.getElementById('btn-flee'),
  encounterAllyBtn: document.getElementById('btn-encounter-ally'),
  movementButtons: Array.from(document.querySelectorAll('.mv'))
};

function apiPost(path, payload) {
  return fetch(`${API}${path}`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload||{})
  }).then(r=>r.json()).catch(e=>({error:true,message:e.message}));
}
function apiGet(path) {
  return fetch(`${API}${path}`).then(r=>r.json()).catch(e=>({error:true,message:e.message}));
}

function logMessage(text, cls='entry') {
  const div = document.createElement('div');
  div.className = cls;
  div.textContent = text;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}
function logCombat(line, cls='combat-round') {
  const div = document.createElement('div');
  div.className = cls;
  div.textContent = line;
  els.combatLog.appendChild(div);
  els.combatLog.scrollTop = els.combatLog.scrollHeight;
}

function updatePlayer(data) {
  if(!data){ return; }
  const p = data.player;
  if(!p){ return; }
  els.playerStats.textContent = `Name: ${p.name}\nHealth: ${p.health}\nGold: ${p.gold}\nFloor: ${p.floor}\nRoom: ${p.room_id}\nAllies: ${p.allies_count}`;
  // Enable movement buttons
  els.movementButtons.forEach(btn=>{
    const dir = btn.dataset.dir;
    btn.disabled = !p.is_alive;
  });
  els.submitScoreBtn.disabled = !p.is_alive;
  els.deleteBtn.disabled = !sessionId;
}
function updateRoom(room) {
  if(!room){ return; }
  els.roomInfo.textContent = `ID: ${room.room_id}\nFloor: ${room.floor}\nStaircase: ${room.has_staircase ? 'Yes':'No'}\nDirections: ${(room.available_directions||[]).join(', ')}\n\n${room.description}`;
  // Only enable staircase button if has one
  const upBtn = els.movementButtons.find(b=>b.dataset.dir==='up');
  if(upBtn){ upBtn.disabled = !room.has_staircase; }
}

function handleEncounter(enc) {
  if(!enc) return;
  const data = enc.data || {};
  // Turn-based battle start
  if(data.battle_started){
    inBattle = true;
    lastEnemy = data.enemy;
    logMessage(data.description || 'Battle begins!', 'encounter');
    els.combatLog.innerHTML = '';
  } else {
    // Auto resolved combat
    lastEnemy = data.enemy || null;
    combatLog = data.combat_log || [];
    if(data.short_summary) logMessage(data.short_summary, 'encounter');
    if(combatLog.length){
      els.combatLog.innerHTML = '';
      combatLog.slice(-10).forEach(r=> logCombat(r.summary || JSON.stringify(r)) );
    }
    inBattle = false;
  }
  updateCombatButtons();
}

function updateCombatButtons(){
  if(inBattle){
    els.attackBtn.disabled = !lastEnemy;
    els.fleeBtn.disabled = !lastEnemy;
    // Ally button available only if ally not used (server tells after attack)
    // We'll enable after each attack response based on ally_available flag.
  } else {
    els.attackBtn.disabled = true;
    els.fleeBtn.disabled = true;
  }
}

function createPlayer(){
  apiPost('/player/new',{name:'Web Delver'}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Error creating player','error');
    sessionId = resp.data.session_id;
    logMessage(resp.message||'Player created');
    updatePlayer(resp.data);
    updateRoom(resp.data.current_room);
    refreshStatus();
    loadScores();
  });
}
function refreshStatus(){
  if(!sessionId){ logMessage('No session. Create player first.'); return; }
  apiPost('/player/status',{session_id:sessionId}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Status error','error');
    updatePlayer(resp.data);
    updateRoom(resp.data.current_room);
  });
}
function move(dir){
  if(!sessionId) return;
  // Request turn-based mode
  apiPost('/player/move',{session_id:sessionId,direction:dir,turn_based:true}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Move failed','error');
    logMessage(resp.message||`Moved ${dir}`);
    // Use enriched data
    updateRoom(resp.data.room_info || resp.data.new_room || resp.data.current_room);
    refreshStatus();
    if(resp.data.encounter_occurred){
      handleEncounter(resp.data.encounter_result);
    } else {
      lastEnemy = null; inBattle = false; updateCombatButtons();
    }
  });
}
function attack(useAlly=false){
  if(!sessionId || !inBattle) return;
  apiPost('/player/attack',{session_id:sessionId,action:'attack',use_ally:useAlly}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Attack failed','error');
    const d = resp.data || {};
    const logLines = d.battle_log || [];
    logLines.forEach(l=> logCombat(l.description || JSON.stringify(l)) );
    if(d.battle_ended){
      inBattle = false;
      if(d.victory){
        logMessage(d.reward?.message || 'Enemy defeated!','encounter');
      } else {
        logMessage('You were defeated!','error');
      }
      lastEnemy = null;
    } else {
      lastEnemy = { name: 'Enemy', health: d.enemy_health }; // minimal snapshot
      if(d.ally_available){ els.allyBtn.disabled = false; } else { els.allyBtn.disabled = true; }
    }
    updateCombatButtons();
    refreshStatus();
  });
}
function useAlly(){ attack(true); }
function flee(){
  if(!sessionId || !inBattle) return;
  apiPost('/player/attack',{session_id:sessionId,action:'flee'}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Flee failed','error');
    logMessage(resp.data?.message || resp.message || 'Fled from battle');
    inBattle = false; lastEnemy = null;
    updateCombatButtons();
    refreshStatus();
  });
}
function encounterAlly(){
  if(!sessionId) return;
  apiPost('/encounter/ally',{session_id:sessionId}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'No ally','error');
    logMessage(resp.message||'Encountered ally','encounter');
    refreshStatus();
  });
}
function submitScore(){
  if(!sessionId) return;
  apiPost('/scores/submit',{session_id:sessionId}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Score submit failed','error');
    logMessage(resp.message||'Score submitted','encounter');
    loadScores();
  });
}
function deletePlayer(){
  if(!sessionId) return;
  apiPost('/player/delete',{session_id:sessionId}).then(resp=>{
    if(resp.error) return logMessage(resp.message||'Delete failed','error');
    logMessage('Player deleted.');
    sessionId=null; lastEnemy=null; combatLog=[];
    els.playerStats.textContent='No player yet.';
    els.roomInfo.textContent='';
    updateCombatButtons();
    els.movementButtons.forEach(b=>b.disabled=true);
    els.submitScoreBtn.disabled=true; els.deleteBtn.disabled=true;
  });
}
function loadScores(){
  apiGet('/scores/highscores').then(resp=>{
    if(resp.error) return; // silent
    const scores = resp.data || [];
    els.highScores.innerHTML = '';
    scores.forEach(s=>{
      const li = document.createElement('li');
      li.textContent = `${s.name} – ${s.gold} gold (floor ${s.floor})`;
      els.highScores.appendChild(li);
    });
  });
}

// Wire events
els.newPlayerBtn.addEventListener('click', createPlayer);
els.refreshBtn.addEventListener('click', refreshStatus);
els.submitScoreBtn.addEventListener('click', submitScore);
els.deleteBtn.addEventListener('click', deletePlayer);
els.attackBtn.addEventListener('click', ()=> attack(false));
els.allyBtn.addEventListener('click', useAlly);
els.fleeBtn.addEventListener('click', flee);
els.encounterAllyBtn.addEventListener('click', encounterAlly);
els.movementButtons.forEach(btn=> btn.addEventListener('click', ()=> move(btn.dataset.dir)) );

// Keyboard shortcuts
window.addEventListener('keydown', (e)=>{
  if(e.key==='n'){ createPlayer(); }
  if(e.key==='r'){ refreshStatus(); }
  if(e.key==='a'){ attack(false); }
  if(e.key==='f'){ flee(); }
  if(e.key==='u'){ useAlly(); }
  if(e.key==='l'){ encounterAlly(); }
  if(['ArrowUp','w','W'].includes(e.key)){ move('north'); }
  if(['ArrowDown','s','S'].includes(e.key)){ move('south'); }
  if(['ArrowLeft','a','A'].includes(e.key)){ move('west'); }
  if(['ArrowRight','d','D'].includes(e.key)){ move('east'); }
});

// Initial load
loadScores();
logMessage('Welcome. Create a player to begin.');
