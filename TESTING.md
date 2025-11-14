# Testing Documentation

## Overview

This document describes the testing strategy and structure for the Abyssal-Invaders dungeon crawler game. The project uses **pytest** as the primary testing framework with comprehensive unit tests that focus on isolating functionality through mocking external dependencies.

## Testing Strategy

### Framework and Tools
- **Testing Framework**: pytest
- **Mocking**: unittest.mock (Mock, patch, MagicMock)
- **Coverage**: pytest-cov for code coverage analysis
- **Dependencies**: pytest-mock for enhanced mocking capabilities

### Testing Principles
1. **Unit Testing Focus**: Each test targets specific functionality in isolation
2. **External Dependency Mocking**: All external dependencies (OpenAI API, file I/O, random functions) are mocked to ensure consistent and reliable test results
3. **Comprehensive Coverage**: Tests cover both positive and negative scenarios, edge cases, and error conditions
4. **Integration Testing**: Selected integration tests verify complete workflows work correctly with real object interactions

## Test Directory Structure

```
/tests/
├── app/
│   └── controllers/
│       ├── test_combat.py          # Comprehensive CombatController tests
│       ├── test_generation.py      # Comprehensive GenerationController tests
│       ├── test_inventory.py       # Comprehensive InventoryController tests
│       ├── test_movement.py        # Comprehensive MovementController tests
│       └── test_scoring.py         # Comprehensive ScoringController tests
└── [other test files...]
```

### Test File Organization
- Test files mirror the project structure under `/tests/app/`
- Each test file corresponds to a project file and is named `test_{project_file_name}.py`
- Test classes are organized by the class or module they test
- Integration tests are included in the same files as unit tests but clearly separated

## CombatController Testing (`test_combat.py`)

### Test Coverage Areas

#### 1. Controller Initialization
- Tests OpenAI client setup (available/unavailable scenarios)
- Verifies proper initialization with and without external dependencies

#### 2. Combat Initiation (`initiate_combat`)
- Player defeat validation (cannot start if already defeated)
- Successful combat scenarios with mocked combat rounds
- Victory and defeat outcome handling

#### 3. Turn-Based Battle System
- `start_battle()`: Battle initialization with and without allies
- `execute_attack()`: Player attacks, ally special attacks, victory/defeat scenarios
- `execute_flee()`: Successful and failed flee attempts

#### 4. AI-Powered Descriptions
- OpenAI integration testing (success, failure, unavailable scenarios)
- Fallback description generation when AI is not available
- Critical hit description generation

#### 5. Combat Mechanics
- Critical hit calculation (10% chance)
- Damage calculation with variance
- Player, enemy, and ally attack execution
- Combat round execution and logging

#### 6. Victory/Defeat Handling
- Player defeat: gold loss, health reset to 1
- Enemy defeat: gold/XP rewards, level up detection, healing items (20% chance)
- Reward calculation and distribution

#### 7. Ally System Integration
- Ally execution with different types (attacker, healer, skipper)
- Ally usage through ally_index parameter instead of current_ally
- One-time ally usage per battle tracking
- Invalid ally selection handling
- Ally persistence (remain in player's allies list after use)

#### 8. Utility Functions
- Encounter chance checking
- Combat description generation
- Damage calculation with various scenarios

## GenerationController Testing (`test_generation.py`)

### Test Coverage Areas

#### 1. Controller Initialization
- OpenAI client setup testing (available, unavailable, configuration failure scenarios)
- Template loading verification for all content types
- Fallback behavior when OpenAI is not configured

#### 2. Enemy Content Generation (`generate_enemy_content`)
- OpenAI integration (success, failure, fallback scenarios)
- Template-based generation with difficulty scaling
- Floor-based enemy selection (basic, intermediate, advanced, legendary)
- Room context integration for contextual generation

#### 3. Ally Content Generation (`generate_ally_content`)
- OpenAI integration testing (success and failure paths)
- Template-based ally generation with appropriate descriptions
- Floor context integration for ally descriptions

#### 4. Room Content Generation (`generate_room_content`)
- **Always uses template-based generation** (OpenAI disabled for rooms)
- Difficulty-based room template selection
- Floor-appropriate room naming and descriptions
- OpenAI client is never called for room generation (by design)

#### 5. Combat Description Generation
- Dynamic combat descriptions for different action types (encounter, victory)
- Player/enemy/room context integration
- Template variety and randomization

#### 6. Helper Methods
- Difficulty modifier calculation (floor-based scaling)
- Room context extraction and formatting
- Individual description generators for enemies, allies, and rooms

#### 7. Template System
- Enemy name templates (4 difficulty levels with 10+ names each)
- Ally name templates (18+ diverse ally types)
- Room name templates (4 difficulty levels with 10+ names each)
- Description templates (atmospheric and dangerous categories)

#### 8. OpenAI Integration Fallbacks
- Graceful degradation when OpenAI API fails
- Exception handling for API errors
- Consistent output format regardless of generation method

## InventoryController Testing (`test_inventory.py`)

### Test Coverage Areas

#### 1. Controller Initialization
- Basic controller setup and configuration
- Item find chance constants verification (BASE_ITEM_FIND_CHANCE = 0.08)

#### 2. Item Finding System (`roll_for_item_find`)
- Successful item discovery with proper probability mocking (8% chance)
- Failed item discovery scenarios (above 0.08 threshold)
- Visited room behavior (no items found in previously visited rooms)
- Random item type generation integration
- Floor-based item selection verification

#### 3. Inventory Management
- Adding items to player inventory through controller
- Auto-consume item handling (dirt_burger with curse effects)
- Item validation and proper response formatting
- Inventory size tracking and response data structure

#### 4. Item Usage System (`use_item`)
- Successful item usage with various item types
- Item consumption after successful use
- Non-existent item handling
- Combat context validation (dirt_burger not usable in combat)
- Enemy interaction for combat items
- Item use failure scenarios and error handling
- Player and enemy stat updates after item use
- Gold coin bag now usable in combat scenarios

#### 5. Inventory Operations
- Getting complete inventory with proper formatting
- Empty inventory handling
- Grouped inventory organization by item type
- Item discarding functionality (success and failure cases)
- Combat-usable item filtering (includes gold_coin_bag now)

#### 6. Item Model Integration
- All item type creation and validation (9 item types including dirt_burger)
- Invalid item type error handling
- Item serialization and deserialization (to_dict/from_dict)
- Item information retrieval (get_item_info)
- Auto-consume property handling

#### 7. Item Effects Testing (Updated Values)
- Health restoration items:
  - health_potion (Emergency Coffee): 15 HP healing
  - greater_health_potion (Energy Drink): 25 HP healing
- Health cap respect (cannot exceed max_health)
- Stat boost items:
  - attack_boost (Motivational Poster): +10 attack
  - defense_boost (Safety Manual): +10 defense
- Damage items:
  - damage_bomb (Exploding Printer Cartridge): 28 damage
  - poison_vial (Expired Vending Machine Soda): 18 damage
- Utility items:
  - gold_coin_bag (Petty Cash Envelope): 50 gold, now usable in combat
  - escape_scroll (Emergency Exit Map): guaranteed flee
- Cursed items:
  - dirt_burger: permanently reduces max HP by 1, auto-consumes
- Item effect result structure validation

#### 8. Player Inventory Integration
- Direct player inventory operations (add, remove, get)
- Inventory persistence through player serialization
- Non-existent item handling in player operations
- Auto-consume item handling in player workflow

#### 9. Random Item Generation
- Floor-based rarity weighting system
- Weighted item selection mocking and verification
- Random item type distribution testing
- Cursed item rarity handling

### Coverage Metrics
- **Code Coverage**: 93.42% (53/56 statements covered)
- **Branch Coverage**: 90% (18/20 branches covered)
- **Test Count**: 32 comprehensive tests
- **Test Categories**: Controller tests (12), Item model tests (13), Integration tests (7)

### Recent Updates (Inventory System Overhaul)
- **Item Find Rate Reduced**: BASE_ITEM_FIND_CHANCE changed from 65% to 8%
- **Healing Values Reduced**: Health potions now heal 15/25 HP (down from 30/60 HP)
- **Attack Boost Reduced**: Attack boost items now provide +10 (down from +15)
- **Damage Values Reduced**: Damage bombs deal 28 damage, poison vials deal 18 damage (down from 40/25)
- **Gold Coin Bag Combat Usable**: Gold coin bags can now be used during combat
- **New Cursed Item**: Added dirt_burger with permanent max HP reduction and auto-consume
- **Thematic Renaming**: All items renamed with office/corporate theme (Emergency Coffee, Motivational Poster, etc.)
- **Auto-Consume System**: New item property for items that are automatically used when found

## MovementController Testing (`test_movement.py`)

### Test Coverage Areas

#### 1. Controller Initialization
- Default RoomDB initialization and custom RoomDB injection
- Session management and session ID configuration
- Room caching system initialization

#### 2. Player Movement System (`move_player`)
- Valid direction movement with bidirectional connections
- Invalid direction handling and error responses
- Room connection validation and traversal
- Direction normalization (north, n, N all work)
- Missing room handling and regeneration
- Current room not found error scenarios

#### 3. Staircase System (`_handle_staircase`)
- Successful floor transitions via staircase
- Staircase presence validation
- Player floor advancement and room reset
- Starting room initialization on new floors

#### 4. Room Management
- Room retrieval from database and cache
- Room saving with database persistence
- Cache management and invalidation
- Session-specific room handling
- Room cache key generation and lookup

#### 5. Floor Generation System
- Complete floor generation with connected rooms
- Room connection algorithms (minimum spanning tree)
- Bidirectional connection establishment
- Staircase placement (exactly one per floor)
- Floor size randomization (5-15 rooms)
- Room ID generation and uniqueness

#### 6. Room Connection Logic (`_connect_floor_rooms`)
- Minimum spanning tree room connectivity
- Bidirectional path creation
- Available direction validation
- Connection conflict resolution

#### 7. Session-Specific Features
- Session-based room storage and retrieval
- Session-specific floor generation with deterministic seeding
- Session cache management and clearing
- Fallback to regular operations without session

#### 8. Room Generation (`_generate_room`)
- Integration with GenerationController for room content
- Encounter chance calculation based on floor
- Ally placement probability (8% chance) using Ally model
- Room property initialization

#### 9. Floor Management
- Floor existence checking and validation
- Complete floor regeneration when rooms are missing
- Staircase validation and placement
- Start room generation for new floors

#### 10. Utility Functions
- Available movement options retrieval
- Player room initialization for new players
- Opposite direction calculation for bidirectional connections
- Direction validation and normalization

#### 11. Error Handling and Edge Cases
- Missing room recovery and regeneration
- Invalid direction inputs
- Database failure scenarios
- Cache inconsistency handling
- Room connection conflicts

### Test Categories

#### Unit Tests (Primary Focus)
- **TestMovementController**: Comprehensive tests for all MovementController methods (39 tests)
- All external dependencies mocked (RoomDB, GenerationController, random functions)
- Individual method behavior testing in isolation
- Edge cases and boundary condition validation
- Error condition and exception handling

#### Edge Case Testing
- **TestMovementControllerEdgeCases**: Complex scenarios and error conditions (8 tests)
- Direction normalization testing (north, n, N all accepted)
- Room generation with different probability scenarios
- Cache behavior under different conditions
- Ally generation probability and content testing

#### Session-Specific Testing
- **TestMovementControllerSessionHandling**: Session-based functionality (4 tests)
- Session-specific room storage and retrieval
- Session-based floor generation with deterministic seeding
- Session cache management and clearing
- Fallback behavior when no session provided

### Coverage Metrics
- **Code Coverage**: 77.46% (255/317 statements covered)
- **Branch Coverage**: 68% (68/100 branches covered)
- **Test Count**: 51 comprehensive tests
- **Test Categories**: Unit tests (39), Edge cases (8), Session handling (4)

### Fixed Issues
- **Import Error Resolution**: Fixed incorrect import of `get_random_room_names` and `get_random_room_descriptions` from movement module
- **Ally Generation Testing**: Updated test to properly mock `Ally.create_random_ally()` method instead of non-existent GenerationController ally method
- **Room Generation Testing**: Corrected test to use GenerationController integration for room content generation
- **Ally System Migration**: Updated combat tests from old `current_ally` system to new `ally_index` parameter system
  - Removed deprecated `_execute_ally_attack` method tests
  - Updated ally usage tests to use real Ally objects instead of mocks
  - Fixed ally persistence behavior (allies remain in player's list after use)
  - Added tests for different ally types (attacker, healer, skipper)

## ScoringController Testing (`test_scoring.py`)

### Test Coverage Areas

#### 1. Controller Initialization
- Default HighScoreDB initialization and custom database injection
- Proper dependency injection verification

#### 2. Gold Reward Calculations (`calculate_enemy_gold_reward`)
- Base reward calculation with floor and difficulty bonuses
- Minimum gold reward enforcement (5 gold minimum)
- Floor scaling validation (higher floors = more gold)
- Enemy stat-based difficulty bonuses

#### 3. Exploration Rewards (`award_exploration_gold`)
- New room exploration gold awards (2 + floor level)
- Previously visited room handling (no gold awarded)
- Floor-based scaling of exploration rewards

#### 4. Floor Completion Bonuses (`award_floor_completion_bonus`)
- Floor completion bonus calculation (floor * 25 gold)
- Progressive bonus scaling for higher floors

#### 5. Survival Bonus System (`calculate_survival_bonus`)
- Health percentage-based survival bonuses
- Room exploration count integration
- Combined health and exploration scoring
- Edge case handling (zero health, full health scenarios)

#### 6. High Score Management
- Score submission with database integration (`submit_high_score`)
- Leaderboard ranking and position calculation
- Success/failure handling for database operations
- Exception handling and error responses

#### 7. High Score Retrieval (`get_high_scores`)
- Formatted leaderboard data retrieval
- Custom limit support for score count
- Score display formatting (rank, name, gold, floor)
- Database error handling and recovery

#### 8. Player Statistics (`get_player_statistics`)
- Comprehensive player stat compilation
- Basic stats (health, gold, floor, attack, defense)
- Progress stats (rooms visited, allies found)
- Calculated stats (health percentage, exploration score, survival score)
- Alive/dead status determination

#### 9. Death Penalty System
- Death penalty calculation (`calculate_death_penalty`)
- Gold loss calculation (25% with 100 gold cap)
- Floor penalty calculation (1 floor loss, minimum floor 1)
- Respawn location and health restoration logic
- Penalty application to player state (`apply_death_penalty`)

#### 10. Score Summary Generation (`get_score_summary`)
- Current session statistics compilation
- Potential bonus calculations integration
- Performance metrics (gold per floor, survival rate, exploration efficiency)
- Division by zero protection for edge cases

#### 11. Utility Functions
- Player rank finding in high score lists (`_find_player_rank`)
- Multiple score matches handling
- Rank calculation and validation

### Test Categories

#### Unit Tests (Primary Focus)
- **TestScoringController**: Comprehensive tests for all ScoringController methods
- All external dependencies mocked (HighScoreDB, helper functions)
- Individual method behavior testing in isolation
- Edge cases and boundary condition validation
- Error condition and exception handling

#### Edge Case Testing
- **TestScoringControllerEdgeCases**: Complex scenarios and error conditions
- Zero stat handling (health, gold, floor level)
- Division by zero protection verification
- Invalid input handling and boundary scenarios
- Dead player statistics and penalty calculations

#### Integration Tests
- **TestScoringControllerIntegration**: End-to-end workflow testing
- Real Player and Enemy object interactions
- Complete scoring workflows (gold calculation → statistics → penalties)
- Realistic game session simulations
- Multi-step scoring processes validation

### Mocking Strategy

#### External Dependencies Mocked
1. **HighScoreDB**: All database operations mocked to prevent file I/O
2. **Helper Functions**: `create_success_response()`, `create_error_response()` mocked for controlled responses
3. **Model Methods**: Player and Enemy method calls controlled for predictable testing
4. **File Operations**: Database load/save operations mocked

#### Real Objects Used
- Player and Enemy model instances for realistic interactions
- Actual scoring calculation logic (not mocked)
- Real helper function responses for integration testing
- Authentic stat modification and penalty applications

### Coverage Metrics
- **Code Coverage**: 100% (76/76 statements covered)
- **Branch Coverage**: 100% (12/12 branches covered)
- **Test Count**: 39 comprehensive tests
- **Test Categories**: Unit tests (26), Edge cases (5), Integration tests (8)

### Test Categories

#### Unit Tests (Primary Focus)
- **TestMovementController**: Comprehensive tests for all MovementController methods
- **TestCombatController**: Comprehensive tests for all CombatController methods
- **TestGenerationController**: Comprehensive tests for all GenerationController methods
- **TestInventoryController**: Comprehensive tests for all InventoryController methods
- **TestItemModel**: Complete Item model functionality testing
- Mocks all external dependencies (OpenAI, random functions, model interactions)
- Tests individual method behavior in isolation
- Covers edge cases, error conditions, and boundary scenarios

#### Edge Case Testing
- **TestMovementControllerEdgeCases**: Tests for complex scenarios and error conditions
- **TestMovementControllerSessionHandling**: Session-specific functionality testing
- Direction normalization and validation edge cases
- Room generation with various probability scenarios
- Cache behavior under different conditions

#### Integration Tests
- **TestCombatControllerIntegration**: End-to-end workflow testing for combat
- **TestGenerationControllerIntegration**: End-to-end workflow testing for content generation
- **TestInventoryControllerIntegration**: End-to-end workflow testing for inventory management
- **TestPlayerInventoryIntegration**: Player inventory operations with real objects
- Uses real model objects (Player, Enemy, Room, Item) without mocking
- Verifies complete workflows (combat flows, content generation consistency, item lifecycles)
- Ensures different components work together correctly

### Mocking Strategy

#### External Dependencies Mocked
1. **OpenAI API**: All `openai_client` calls mocked to prevent API calls during testing
2. **Random Functions**: `random.random()`, `random.choice()`, `random.randint()` controlled for predictable outcomes
3. **Utility Functions**: `calculate_damage_with_variance()`, `roll_dice()` mocked for controlled results
4. **Model Methods**: Specific model methods mocked when testing controller logic in isolation
5. **OpenAI Client Creation**: `create_openai_client()` mocked to control client availability scenarios
6. **Item Generation**: `Item.get_random_item_type()` mocked for predictable item creation
7. **Database Operations**: `RoomDB` operations mocked to prevent file I/O during testing
8. **Floor Generation**: `generate_room_id()`, room name/description generators mocked for predictable outcomes
9. **Hash Functions**: `hashlib.md5()` mocked for session-based seeding scenarios

#### Real Objects Used
- Player, Enemy, Room, Item model instances used to test actual object interactions
- Helper functions from utils module used to test real integration
- Template data systems tested with real data structures
- Item effect systems tested with real stat modifications

## Running Tests

### Prerequisites
```bash
pip install pytest pytest-cov pytest-mock
```

### Basic Test Execution
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/app/controllers/test_combat.py
pytest tests/app/controllers/test_generation.py
pytest tests/app/controllers/test_inventory.py
pytest tests/app/controllers/test_movement.py
pytest tests/app/controllers/test_scoring.py

# Run tests with coverage
pytest --cov=app/controllers/combat tests/app/controllers/test_combat.py
pytest --cov=app/controllers/generation tests/app/controllers/test_generation.py
pytest --cov=app/controllers/inventory tests/app/controllers/test_inventory.py
pytest --cov=app/controllers/movement tests/app/controllers/test_movement.py
pytest --cov=app/controllers/scoring tests/app/controllers/test_scoring.py

# Run tests with detailed coverage report
pytest --cov=app/controllers/combat --cov-report=html tests/app/controllers/test_combat.py
pytest --cov=app/controllers/generation --cov-report=html tests/app/controllers/test_generation.py
pytest --cov=app/controllers/inventory --cov-report=html tests/app/controllers/test_inventory.py
pytest --cov=app/controllers/movement --cov-report=html tests/app/controllers/test_movement.py
pytest --cov=app/controllers/scoring --cov-report=html tests/app/controllers/test_scoring.py
```

### Test Output
Tests provide detailed feedback on:
- Test success/failure status
- Code coverage percentages
- Missing coverage areas
- Assertion failures with detailed error messages

## Test Quality Metrics

### Current Coverage Goals
- **Target Coverage**: >90% for all tested modules
- **Critical Path Coverage**: 100% for main combat workflows
- **Edge Case Coverage**: All error conditions and boundary scenarios tested

### Test Reliability
- All tests are deterministic (no random failures)
- Tests run independently (no test interdependencies)
- Consistent results across different environments
- Fast execution (all external calls mocked)

## Best Practices Followed

1. **Descriptive Test Names**: Each test clearly describes what scenario it's testing
2. **Arrange-Act-Assert Pattern**: Tests follow clear setup, execution, and verification phases
3. **Single Responsibility**: Each test focuses on one specific behavior
4. **Comprehensive Assertions**: Tests verify both expected outcomes and side effects
5. **Error Testing**: Negative scenarios and error conditions are thoroughly tested
6. **Documentation**: Each test includes docstrings explaining the test purpose

## Future Testing Considerations

1. **Performance Testing**: Add tests for combat performance under high load
2. **Stress Testing**: Test with extreme values (very high/low stats)
3. **Compatibility Testing**: Ensure tests work across different Python versions
4. **Property-Based Testing**: Consider using Hypothesis for generating test scenarios

---

*Last Updated: November 14, 2025*
*Framework: pytest*
*Coverage: combat.py, generation.py, inventory.py, movement.py, scoring.py - Comprehensive unit and integration testing*