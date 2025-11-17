"""
Office-themed elemental system for the dungeon crawler game.
Elements represent different office departments with advantages and disadvantages.
"""

from typing import Optional, Dict

# Office Department Elements
ELEMENTS = {
    "accounting": {
        "name": "Accounting",
        "emoji": "📊",
        "color": "#2ecc71",
        "description": "Masters of numbers and spreadsheets",
        "strong_against": ["marketing", "hr"],  # Accounting cuts marketing budgets and questions HR spending
        "weak_against": ["it", "management"]    # IT controls their systems, management overrides decisions
    },
    "it": {
        "name": "IT",
        "emoji": "💻",
        "color": "#3498db",
        "description": "Controllers of technology and systems",
        "strong_against": ["accounting", "sales"],  # IT controls accounting systems and sales tools
        "weak_against": ["hr", "marketing"]         # HR handles IT complaints, marketing demands take priority
    },
    "marketing": {
        "name": "Marketing",
        "emoji": "📱",
        "color": "#e74c3c",
        "description": "Creative visionaries and brand builders",
        "strong_against": ["it", "legal"],          # Marketing pushes IT for features, bypasses legal with "industry standard"
        "weak_against": ["accounting", "management"] # Accounting cuts budgets, management redirects vision
    },
    "hr": {
        "name": "HR",
        "emoji": "👔",
        "color": "#9b59b6",
        "description": "Guardians of workplace harmony",
        "strong_against": ["it", "management"],     # HR mediates IT disputes, holds management accountable
        "weak_against": ["accounting", "legal"]     # Accounting questions HR costs, legal overrules HR policies
    },
    "sales": {
        "name": "Sales",
        "emoji": "💼",
        "color": "#f39c12",
        "description": "Revenue generators and deal closers",
        "strong_against": ["hr", "legal"],          # Sales bypasses HR processes, pressures legal for faster deals
        "weak_against": ["it", "accounting"]        # IT prioritizes internal projects, accounting audits expenses
    },
    "legal": {
        "name": "Legal",
        "emoji": "⚖️",
        "color": "#34495e",
        "description": "Enforcers of compliance and contracts",
        "strong_against": ["accounting", "sales"],  # Legal audits accounting practices, blocks risky sales deals
        "weak_against": ["marketing", "management"] # Marketing finds workarounds, management pressures decisions
    },
    "management": {
        "name": "Management",
        "emoji": "👨‍💼",
        "color": "#1abc9c",
        "description": "Strategic leaders and decision makers",
        "strong_against": ["marketing", "sales"],   # Management directs marketing strategy, sets sales quotas
        "weak_against": ["hr", "it"]                # HR enforces policies on management, IT controls their access
    },
    "intern": {
        "name": "Intern",
        "emoji": "☕",
        "color": "#95a5a6",
        "description": "Eager learners, unpredictable wildcards",
        "strong_against": [],  # No advantages - they're learning
        "weak_against": []     # No weaknesses - they're too naive to care
    }
}

# Damage multipliers
ADVANTAGE_MULTIPLIER = 1.25  # 25% more damage when strong against
DISADVANTAGE_MULTIPLIER = 0.8  # 20% less damage when weak against
NEUTRAL_MULTIPLIER = 1.0  # Normal damage


def get_element_effectiveness(attacker_element: str, defender_element: str) -> float:
    """
    Calculate damage multiplier based on elemental matchup.
    
    Args:
        attacker_element (str): Element of the attacker
        defender_element (str): Element of the defender
        
    Returns:
        float: Damage multiplier (0.8, 1.0, or 1.25)
    """
    # Intern is always neutral
    if attacker_element == "intern" or defender_element == "intern":
        return NEUTRAL_MULTIPLIER
    
    # Check if elements exist
    if attacker_element not in ELEMENTS or defender_element not in ELEMENTS:
        return NEUTRAL_MULTIPLIER
    
    attacker_data = ELEMENTS[attacker_element]
    
    # Check advantage
    if defender_element in attacker_data["strong_against"]:
        return ADVANTAGE_MULTIPLIER
    
    # Check disadvantage
    if defender_element in attacker_data["weak_against"]:
        return DISADVANTAGE_MULTIPLIER
    
    return NEUTRAL_MULTIPLIER


def get_element_matchup_text(attacker_element: str, defender_element: str) -> Optional[str]:
    """
    Get descriptive text for elemental matchup.
    
    Args:
        attacker_element (str): Element of the attacker
        defender_element (str): Element of the defender
        
    Returns:
        Optional[str]: Description of the matchup, or None if neutral
    """
    effectiveness = get_element_effectiveness(attacker_element, defender_element)
    
    if effectiveness == ADVANTAGE_MULTIPLIER:
        return "**EFFECTIVE!** Office politics favor this attack! (+25% damage)"
    elif effectiveness == DISADVANTAGE_MULTIPLIER:
        return "*Not very effective...* Organizational hierarchy resists! (-20% damage)"
    
    return None


def get_element_info(element: str) -> Optional[Dict]:
    """
    Get information about an element.
    
    Args:
        element (str): Element key
        
    Returns:
        Optional[Dict]: Element data or None if not found
    """
    return ELEMENTS.get(element)


def get_all_elements() -> Dict:
    """
    Get all available elements.
    
    Returns:
        Dict: All elements data
    """
    return ELEMENTS.copy()
