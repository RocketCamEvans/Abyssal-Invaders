"""
Blackjack controller for casino gameplay.
"""

import random
from typing import List, Tuple, Dict, Any


class BlackjackController:
    """
    Handles blackjack game logic.
    """
    
    def __init__(self):
        """Initialize the blackjack controller."""
        pass
    
    def create_deck(self) -> List[Dict[str, Any]]:
        """
        Create a standard 52-card deck.
        
        Returns:
            List[Dict[str, Any]]: List of card dictionaries
        """
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        deck = []
        for suit in suits:
            for rank in ranks:
                # Determine card value
                if rank in ['J', 'Q', 'K']:
                    value = 10
                elif rank == 'A':
                    value = 11  # Aces start as 11, can be 1
                else:
                    value = int(rank)
                
                deck.append({
                    'rank': rank,
                    'suit': suit,
                    'value': value,
                    'display': f"{rank}{suit}"
                })
        
        random.shuffle(deck)
        return deck
    
    def calculate_hand_value(self, hand: List[Dict[str, Any]]) -> int:
        """
        Calculate the total value of a hand, accounting for Aces.
        
        Args:
            hand (List[Dict[str, Any]]): List of cards in hand
            
        Returns:
            int: Total hand value
        """
        total = sum(card['value'] for card in hand)
        aces = sum(1 for card in hand if card['rank'] == 'A')
        
        # Convert Aces from 11 to 1 if busting
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def start_game(self, bet: int) -> Dict[str, Any]:
        """
        Start a new blackjack game.
        
        Args:
            bet (int): Amount of gold bet
            
        Returns:
            Dict[str, Any]: Game state
        """
        deck = self.create_deck()
        
        # Deal initial cards
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        player_value = self.calculate_hand_value(player_hand)
        dealer_value = self.calculate_hand_value(dealer_hand)
        
        # Check for natural blackjack
        player_blackjack = player_value == 21
        dealer_blackjack = dealer_value == 21
        
        # Check if player can split (two cards with same rank)
        can_split = len(player_hand) == 2 and player_hand[0]['rank'] == player_hand[1]['rank']
        
        # Check if player can double down (initial hand only)
        can_double = len(player_hand) == 2
        
        game_state = {
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'bet': bet,
            'player_value': player_value,
            'dealer_value': dealer_value,
            'game_over': player_blackjack or dealer_blackjack,
            'result': None,
            'can_split': can_split,
            'can_double': can_double,
            'is_split': False,
            'split_hand': None,
            'split_value': None,
            'active_hand': 'main',  # 'main' or 'split'
            'doubled': False
        }
        
        # Determine result if someone has blackjack
        if player_blackjack and dealer_blackjack:
            game_state['result'] = 'push'
            game_state['payout'] = bet
            game_state['message'] = 'Both have Blackjack! Push - bet returned.'
        elif player_blackjack:
            game_state['result'] = 'blackjack'
            game_state['payout'] = int(bet * 2.5)  # Blackjack pays 3:2
            game_state['message'] = '🎰 BLACKJACK! You win 2.5x your bet!'
        elif dealer_blackjack:
            game_state['result'] = 'loss'
            game_state['payout'] = 0
            game_state['message'] = 'Dealer has Blackjack. You lose.'
        
        return game_state
    
    def hit(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Player draws another card.
        
        Args:
            game_state (Dict[str, Any]): Current game state
            
        Returns:
            Dict[str, Any]: Updated game state
        """
        if game_state['game_over']:
            return game_state
        
        # Determine which hand to hit
        if game_state.get('is_split') and game_state['active_hand'] == 'split':
            hand = game_state['split_hand']
        else:
            hand = game_state['player_hand']
        
        # Draw a card
        card = game_state['deck'].pop()
        hand.append(card)
        
        # Calculate new hand value
        hand_value = self.calculate_hand_value(hand)
        
        if game_state.get('is_split') and game_state['active_hand'] == 'split':
            game_state['split_value'] = hand_value
        else:
            game_state['player_value'] = hand_value
        
        # Can no longer split or double after hitting
        game_state['can_split'] = False
        game_state['can_double'] = False
        
        # Check for bust
        if hand_value > 21:
            if game_state.get('is_split') and game_state['active_hand'] == 'main':
                # First hand busted, move to split hand
                game_state['active_hand'] = 'split'
                game_state['message'] = f'Main hand busts with {hand_value}. Playing split hand...'
            elif game_state.get('is_split') and game_state['active_hand'] == 'split':
                # Split hand busted, game over
                game_state['game_over'] = True
                # Determine final result based on both hands
                self._finalize_split_game(game_state)
            else:
                # Single hand busted
                game_state['game_over'] = True
                game_state['result'] = 'bust'
                game_state['payout'] = 0
                game_state['message'] = f'Bust! You went over 21 with {hand_value}. You lose.'
        
        return game_state
    
    def stand(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Player stands - dealer plays their hand.
        
        Args:
            game_state (Dict[str, Any]): Current game state
            
        Returns:
            Dict[str, Any]: Updated game state with final result
        """
        if game_state['game_over']:
            return game_state
        
        # If playing split hands and on main hand, switch to split hand
        if game_state.get('is_split') and game_state['active_hand'] == 'main':
            game_state['active_hand'] = 'split'
            game_state['can_split'] = False
            game_state['can_double'] = False
            game_state['message'] = 'Main hand stands. Playing split hand...'
            return game_state
        
        # Dealer draws until 17 or higher
        while self.calculate_hand_value(game_state['dealer_hand']) < 17:
            card = game_state['deck'].pop()
            game_state['dealer_hand'].append(card)
        
        dealer_value = self.calculate_hand_value(game_state['dealer_hand'])
        game_state['dealer_value'] = dealer_value
        game_state['game_over'] = True
        
        # Handle split hand results
        if game_state.get('is_split'):
            self._finalize_split_game(game_state)
        else:
            # Single hand game
            player_value = game_state['player_value']
            bet = game_state['bet']
            
            # Apply double down multiplier
            multiplier = 2 if game_state.get('doubled') else 1
            
            # Determine winner
            if dealer_value > 21:
                game_state['result'] = 'win'
                game_state['payout'] = bet * 2 * multiplier
                game_state['message'] = f'Dealer busts with {dealer_value}! You win {bet * multiplier} gold!'
            elif player_value > dealer_value:
                game_state['result'] = 'win'
                game_state['payout'] = bet * 2 * multiplier
                game_state['message'] = f'You win with {player_value} vs {dealer_value}! Won {bet * multiplier} gold!'
            elif player_value < dealer_value:
                game_state['result'] = 'loss'
                game_state['payout'] = 0
                game_state['message'] = f'Dealer wins with {dealer_value} vs {player_value}. You lose.'
            else:
                game_state['result'] = 'push'
                game_state['payout'] = bet * multiplier
                game_state['message'] = f'Push! Both have {player_value}. Bet returned.'
        
        return game_state
    
    def split(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Split the player's hand into two separate hands.
        
        Args:
            game_state (Dict[str, Any]): Current game state
            
        Returns:
            Dict[str, Any]: Updated game state with split hands
        """
        if game_state['game_over'] or not game_state.get('can_split'):
            return game_state
        
        # Split the hand
        card1 = game_state['player_hand'][0]
        card2 = game_state['player_hand'][1]
        
        game_state['player_hand'] = [card1]
        game_state['split_hand'] = [card2]
        
        # Deal one card to each hand
        game_state['player_hand'].append(game_state['deck'].pop())
        game_state['split_hand'].append(game_state['deck'].pop())
        
        # Calculate values
        game_state['player_value'] = self.calculate_hand_value(game_state['player_hand'])
        game_state['split_value'] = self.calculate_hand_value(game_state['split_hand'])
        
        # Update state
        game_state['is_split'] = True
        game_state['active_hand'] = 'main'
        game_state['can_split'] = False
        game_state['can_double'] = False  # Can't double after split in this implementation
        game_state['message'] = 'Hand split! Playing main hand first...'
        
        # Check for immediate bust on either hand
        if game_state['player_value'] > 21:
            game_state['active_hand'] = 'split'
            game_state['message'] = f'Main hand busts with {game_state["player_value"]}. Playing split hand...'
        
        return game_state
    
    def double_down(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Double the bet, draw one card, and stand.
        
        Args:
            game_state (Dict[str, Any]): Current game state
            
        Returns:
            Dict[str, Any]: Updated game state
        """
        if game_state['game_over'] or not game_state.get('can_double'):
            return game_state
        
        # Double the bet
        game_state['bet'] *= 2
        game_state['doubled'] = True
        game_state['can_double'] = False
        game_state['can_split'] = False
        
        # Draw exactly one card
        card = game_state['deck'].pop()
        game_state['player_hand'].append(card)
        
        # Calculate new hand value
        player_value = self.calculate_hand_value(game_state['player_hand'])
        game_state['player_value'] = player_value
        
        # Check for bust
        if player_value > 21:
            game_state['game_over'] = True
            game_state['result'] = 'bust'
            game_state['payout'] = 0
            game_state['message'] = f'Bust! You went over 21 with {player_value}. You lose double bet.'
        else:
            # Automatically stand after double down
            game_state['message'] = f'Doubled down! Drew {card["display"]}, now at {player_value}. Standing...'
            # Call stand to complete the game
            return self.stand(game_state)
        
        return game_state
    
    def _finalize_split_game(self, game_state: Dict[str, Any]) -> None:
        """
        Calculate final result for split hand game.
        
        Args:
            game_state (Dict[str, Any]): Current game state
        """
        dealer_value = game_state['dealer_value']
        main_value = game_state['player_value']
        split_value = game_state['split_value']
        bet = game_state['bet']
        
        main_result = None
        split_result = None
        main_payout = 0
        split_payout = 0
        
        # Evaluate main hand
        if main_value > 21:
            main_result = 'bust'
            main_payout = 0
        elif dealer_value > 21:
            main_result = 'win'
            main_payout = bet * 2
        elif main_value > dealer_value:
            main_result = 'win'
            main_payout = bet * 2
        elif main_value < dealer_value:
            main_result = 'loss'
            main_payout = 0
        else:
            main_result = 'push'
            main_payout = bet
        
        # Evaluate split hand
        if split_value > 21:
            split_result = 'bust'
            split_payout = 0
        elif dealer_value > 21:
            split_result = 'win'
            split_payout = bet * 2
        elif split_value > dealer_value:
            split_result = 'win'
            split_payout = bet * 2
        elif split_value < dealer_value:
            split_result = 'loss'
            split_payout = 0
        else:
            split_result = 'push'
            split_payout = bet
        
        total_payout = main_payout + split_payout
        game_state['payout'] = total_payout
        
        # Create result message
        main_msg = f"Main hand ({main_value}): {main_result}"
        split_msg = f"Split hand ({split_value}): {split_result}"
        
        if total_payout == 0:
            game_state['result'] = 'loss'
            game_state['message'] = f'{main_msg}, {split_msg}. You lose both hands.'
        elif total_payout == bet * 4:
            game_state['result'] = 'win'
            game_state['message'] = f'{main_msg}, {split_msg}. You win both hands! +{bet * 2} gold!'
        else:
            game_state['result'] = 'split'
            net = total_payout - (bet * 2)
            if net > 0:
                game_state['message'] = f'{main_msg}, {split_msg}. Net: +{net} gold!'
            elif net < 0:
                game_state['message'] = f'{main_msg}, {split_msg}. Net: {net} gold.'
            else:
                game_state['message'] = f'{main_msg}, {split_msg}. Break even.'
    
    def get_game_display(self, game_state: Dict[str, Any], hide_dealer: bool = True) -> Dict[str, Any]:
        """
        Get a display-friendly version of the game state.
        
        Args:
            game_state (Dict[str, Any]): Current game state
            hide_dealer (bool): Whether to hide dealer's second card
            
        Returns:
            Dict[str, Any]: Display data
        """
        player_cards = [card['display'] for card in game_state['player_hand']]
        dealer_cards = [card['display'] for card in game_state['dealer_hand']]
        
        # Hide dealer's second card if game is not over
        if hide_dealer and not game_state['game_over']:
            dealer_display = [dealer_cards[0], '??']
            dealer_value_display = game_state['dealer_hand'][0]['value']
        else:
            dealer_display = dealer_cards
            dealer_value_display = game_state['dealer_value']
        
        display_data = {
            'player_cards': player_cards,
            'dealer_cards': dealer_display,
            'player_value': game_state['player_value'],
            'dealer_value': dealer_value_display if not hide_dealer or game_state['game_over'] else '?',
            'bet': game_state['bet'],
            'game_over': game_state['game_over'],
            'result': game_state.get('result'),
            'payout': game_state.get('payout'),
            'message': game_state.get('message', ''),
            'can_split': game_state.get('can_split', False),
            'can_double': game_state.get('can_double', False),
            'is_split': game_state.get('is_split', False),
            'active_hand': game_state.get('active_hand', 'main')
        }
        
        # Add split hand info if applicable
        if game_state.get('is_split'):
            split_cards = [card['display'] for card in game_state['split_hand']]
            display_data['split_cards'] = split_cards
            display_data['split_value'] = game_state['split_value']
        
        return display_data
