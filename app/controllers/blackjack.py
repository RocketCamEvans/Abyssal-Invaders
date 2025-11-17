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
        
        game_state = {
            'deck': deck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand,
            'bet': bet,
            'player_value': player_value,
            'dealer_value': dealer_value,
            'game_over': player_blackjack or dealer_blackjack,
            'result': None
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
        
        # Draw a card
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
            game_state['message'] = f'Bust! You went over 21 with {player_value}. You lose.'
        
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
        
        # Dealer draws until 17 or higher
        while self.calculate_hand_value(game_state['dealer_hand']) < 17:
            card = game_state['deck'].pop()
            game_state['dealer_hand'].append(card)
        
        player_value = game_state['player_value']
        dealer_value = self.calculate_hand_value(game_state['dealer_hand'])
        game_state['dealer_value'] = dealer_value
        game_state['game_over'] = True
        
        bet = game_state['bet']
        
        # Determine winner
        if dealer_value > 21:
            game_state['result'] = 'win'
            game_state['payout'] = bet * 2
            game_state['message'] = f'Dealer busts with {dealer_value}! You win {bet} gold!'
        elif player_value > dealer_value:
            game_state['result'] = 'win'
            game_state['payout'] = bet * 2
            game_state['message'] = f'You win with {player_value} vs {dealer_value}! Won {bet} gold!'
        elif player_value < dealer_value:
            game_state['result'] = 'loss'
            game_state['payout'] = 0
            game_state['message'] = f'Dealer wins with {dealer_value} vs {player_value}. You lose.'
        else:
            game_state['result'] = 'push'
            game_state['payout'] = bet
            game_state['message'] = f'Push! Both have {player_value}. Bet returned.'
        
        return game_state
    
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
        
        return {
            'player_cards': player_cards,
            'dealer_cards': dealer_display,
            'player_value': game_state['player_value'],
            'dealer_value': dealer_value_display if not hide_dealer or game_state['game_over'] else '?',
            'bet': game_state['bet'],
            'game_over': game_state['game_over'],
            'result': game_state.get('result'),
            'payout': game_state.get('payout'),
            'message': game_state.get('message', '')
        }
