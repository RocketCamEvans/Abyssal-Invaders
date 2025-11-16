# Developer Mode - Quick Reference

## Accessing Developer Tools

1. **Dev Key**: Set in `.env` file as `DEV_MODE_KEY`
   - Default key: `abyssal_dev_2024`

2. **Access URL**: 
   ```
   http://localhost:5000/dev?key=abyssal_dev_2024
   ```

3. **Enable Developer Mode**:
   - Ensure `DEV_MODE_KEY` is set in `.env`
   - Restart the server
   - Look for message: `✓ Developer mode enabled (access with /dev?key=...)`

## Features

### 🛠️ Dev Screen Tools

#### ⚔️ Spawn Battle
- Create instant battles for testing
- Customize floor level
- Set specific enemy names/descriptions
- Or generate random enemies

#### 📊 Modify Player Stats
- Instantly change health, gold, attack, defense, speed
- Test different stat combinations
- Adjust level and floor

#### 🧪 Inflict Ailments
- Test poison and paralysis mechanics
- Apply to player or enemy
- Set severity levels (0-5)
- Works during active battles

#### 🤝 Give Allies
- Instantly add any ally to party
- Browse all available allies
- Test caster allies (poison/paralysis inflictors)
- Bypass encounter requirements

#### 🏛️ Spawn Rooms
- Create specific room types:
  - Normal rooms
  - Shop rooms
  - Stairs rooms
- Set custom floor levels

#### 🎮 Battle Controls
- Force end battles instantly
- Skip to victory/defeat
- Reset battle state

## API Endpoints

All endpoints require the dev key in the request.

### POST /dev/spawn-battle
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024",
  "floor": 5,
  "enemy_name": "Optional Custom Name",
  "enemy_description": "Optional description"
}
```

### POST /dev/modify-stats
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024",
  "health": 200,
  "attack_power": 50,
  "defense": 25,
  "speed": 20
}
```

### POST /dev/inflict-ailment
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024",
  "target": "enemy",
  "ailment_type": "poison",
  "severity": 5
}
```

### POST /dev/give-ally
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024",
  "ally_name": "Venomous Vivian"
}
```

### POST /dev/spawn-room
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024",
  "room_type": "shop",
  "floor": 3
}
```

### POST /dev/end-battle
```json
{
  "session_id": "your-session-id",
  "key": "abyssal_dev_2024"
}
```

### GET /dev/list-allies?key=abyssal_dev_2024
Returns list of all predefined allies.

## Tips

1. **Open from Game**: Open dev tools in a new window while playing to automatically sync session ID
2. **Manual Session ID**: If needed, copy session ID from browser localStorage
3. **Reload Game**: Changes take effect immediately - click "Reload" in the game if needed
4. **Test Ailments**: Use dev tools to test poison/paralysis mechanics in battles
5. **Speed Testing**: Modify speed stats to test double-attack mechanics (3x speed difference)

## Security Note

⚠️ **NEVER** share your `DEV_MODE_KEY` publicly or commit it to version control with sensitive values.
⚠️ Only enable dev mode in development/testing environments.
⚠️ Remove or change the key before production deployment.
