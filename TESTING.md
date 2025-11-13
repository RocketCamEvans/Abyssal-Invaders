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
│       └── test_combat.py          # Comprehensive CombatController tests
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
- Ally attack execution with special damage bonuses
- One-time ally usage tracking
- Invalid ally selection handling

#### 8. Utility Functions
- Encounter chance checking
- Combat description generation
- Damage calculation with various scenarios

### Test Categories

#### Unit Tests (Primary Focus)
- **TestCombatController**: Comprehensive tests for all CombatController methods
- Mocks all external dependencies (OpenAI, random functions, model interactions)
- Tests individual method behavior in isolation
- Covers edge cases, error conditions, and boundary scenarios

#### Integration Tests
- **TestCombatControllerIntegration**: End-to-end workflow testing
- Uses real model objects (Player, Enemy, Room) without mocking
- Verifies complete combat flows (player victory, player defeat, turn-based battles)
- Ensures different components work together correctly

### Mocking Strategy

#### External Dependencies Mocked
1. **OpenAI API**: All `openai_client` calls mocked to prevent API calls during testing
2. **Random Functions**: `random.random()`, `random.choice()`, `random.randint()` controlled for predictable outcomes
3. **Utility Functions**: `calculate_damage_with_variance()`, `roll_dice()` mocked for controlled results
4. **Model Methods**: Specific model methods mocked when testing controller logic in isolation

#### Real Objects Used
- Player, Enemy, Room model instances used to test actual object interactions
- Helper functions from utils module used to test real integration

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

# Run tests with coverage
pytest --cov=app/controllers/combat tests/app/controllers/test_combat.py

# Run tests with detailed coverage report
pytest --cov=app/controllers/combat --cov-report=html tests/app/controllers/test_combat.py
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

*Last Updated: November 13, 2025*
*Framework: pytest*
*Coverage: combat.py - Comprehensive unit and integration testing*