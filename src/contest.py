from datetime import datetime
import random
import string
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import Contest, Player, Trade, Position, ContestStatus

def generate_join_code(length: int = 6) -> str:
    """Generate a random alphanumeric join code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class ContestManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_contest(self, name: str, win_condition: str, starting_balance: float = 10000.0) -> Contest:
        """Create a new contest with a unique join code."""
        join_code = generate_join_code()
        while self.db.query(Contest).filter_by(join_code=join_code).first():
            join_code = generate_join_code()

        contest = Contest(
            name=name,
            join_code=join_code,
            win_condition=win_condition,
            starting_balance=starting_balance,
            status=ContestStatus.ACTIVE
        )
        self.db.add(contest)
        self.db.commit()
        return contest

    def join_contest(self, join_code: str, player_name: str) -> Optional[Player]:
        """Add a player to a contest using the join code."""
        contest = self.db.query(Contest).filter_by(
            join_code=join_code,
            status=ContestStatus.ACTIVE
        ).first()
        
        if not contest:
            return None

        player = Player(
            name=player_name,
            contest_id=contest.id,
            starting_balance=contest.starting_balance,
            cash_balance=contest.starting_balance
        )
        self.db.add(player)
        self.db.commit()
        return player

    def get_player_positions(self, player_id: int) -> List[Dict]:
        """Get current positions for a player."""
        positions = self.db.query(Position).filter_by(player_id=player_id).all()
        return [
            {
                "ticker": pos.ticker,
                "quantity": pos.quantity,
                "avg_price": pos.average_price,
                "current_price": pos.current_price,
                "market_value": pos.quantity * pos.current_price,
                "unrealized_pl": (pos.current_price - pos.average_price) * pos.quantity
            }
            for pos in positions
        ]

    def get_player_trades(self, player_id: int) -> List[Dict]:
        """Get trade history for a player."""
        trades = self.db.query(Trade).filter_by(player_id=player_id).order_by(Trade.trade_date.desc()).all()
        return [
            {
                "date": trade.trade_date,
                "type": trade.type,
                "ticker": trade.ticker,
                "quantity": trade.quantity,
                "price": trade.price,
                "total": trade.total_amount
            }
            for trade in trades
        ]

    def get_leaderboard(self, contest_id: int) -> List[dict]:
        """Get the current leaderboard for a contest."""
        players = self.db.query(Player).filter_by(contest_id=contest_id).all()
        leaderboard = []
        
        for player in players:
            positions = self.get_player_positions(player.id)
            trades = self.get_player_trades(player.id)
            
            # Calculate total portfolio value
            portfolio_value = player.cash_balance + sum(pos["market_value"] for pos in positions)
            unrealized_pl = sum(pos["unrealized_pl"] for pos in positions)
            
            leaderboard.append({
                "name": player.name,
                "cash_balance": player.cash_balance,
                "portfolio_value": portfolio_value,
                "total_profit": portfolio_value - player.starting_balance,
                "unrealized_pl": unrealized_pl,
                "positions": positions,
                "trades": trades
            })
        
        return sorted(leaderboard, key=lambda x: x["total_profit"], reverse=True)

    def get_active_contests(self) -> List[Contest]:
        """Get all active contests."""
        return self.db.query(Contest).filter_by(status=ContestStatus.ACTIVE).all()

    def get_contest_players(self, contest_id: int) -> List[Player]:
        """Get all players in a contest."""
        return self.db.query(Player).filter_by(contest_id=contest_id).all()

    def get_contest_trades(self, contest_id: int) -> List[Dict[str, Any]]:
        """Get all trades for a contest, ordered by date."""
        trades = (
            self.db.query(Trade, Player.name.label("player_name"))
            .join(Player)
            .filter(Player.contest_id == contest_id)
            .order_by(Trade.trade_date.desc())
            .all()
        )
        
        return [{
            "player": trade.player_name,
            "ticker": trade.Trade.ticker,
            "type": trade.Trade.type,
            "quantity": abs(trade.Trade.quantity),  # Show absolute value
            "price": trade.Trade.price,
            "total": trade.Trade.total_amount,
            "date": trade.Trade.trade_date
        } for trade in trades]

    def update_position(self, player_id: int, ticker: str, trade_type: str, 
                       quantity: float, price: float) -> Optional[Position]:
        """Update a player's position after a trade."""
        position = self.db.query(Position).filter_by(
            player_id=player_id,
            ticker=ticker
        ).first()

        if trade_type == "BUY":
            if position:
                # Update existing position
                new_quantity = position.quantity + quantity
                position.average_price = (
                    (position.quantity * position.average_price) + (quantity * price)
                ) / new_quantity
                position.quantity = new_quantity
                position.current_price = price
            else:
                # Create new position
                position = Position(
                    player_id=player_id,
                    ticker=ticker,
                    quantity=quantity,
                    average_price=price,
                    current_price=price
                )
                self.db.add(position)
        else:  # SELL
            if not position or position.quantity < quantity:
                return None
            
            position.quantity -= quantity
            position.current_price = price
            
            if position.quantity == 0:
                self.db.delete(position)

        self.db.commit()
        return position

    def record_trade(self, player_id: int, trade_data: dict) -> Optional[Trade]:
        """Record a new trade for a player and update their position."""
        player = self.db.query(Player).filter_by(id=player_id).first()
        if not player:
            return None

        total_amount = trade_data["quantity"] * trade_data["price"]
        
        # Validate trade
        if trade_data["trade_type"] == "BUY" and total_amount > player.cash_balance:
            return None  # Insufficient funds
        
        # Create trade record
        trade = Trade(
            player_id=player_id,
            ticker=trade_data["ticker"],
            quantity=trade_data["quantity"],
            price=trade_data["price"],
            type=trade_data["trade_type"],
            total_amount=total_amount,
            trade_date=trade_data.get("date", datetime.utcnow())
        )
        
        # Update player's cash balance
        if trade_data["trade_type"] == "BUY":
            player.cash_balance -= total_amount
        else:
            player.cash_balance += total_amount
        
        # Update position
        position = self.update_position(
            player_id,
            trade_data["ticker"],
            trade_data["trade_type"],
            trade_data["quantity"],
            trade_data["price"]
        )
        
        if position is not None:
            self.db.add(trade)
            self.db.commit()
            return trade
        
        return None

    def process_trade(self, player_id: int, ticker: str, trade_type: str, quantity: float, price: float, trade_date: datetime) -> Optional[Trade]:
        """Process a new trade for a player."""
        try:
            print(f"Processing trade - Player: {player_id}, Ticker: {ticker}, Type: {trade_type}, Qty: {quantity}, Price: {price}, Date: {trade_date}")
            
            player = self.db.query(Player).filter_by(id=player_id).first()
            if not player:
                print(f"Error: Player {player_id} not found")
                return None
                
            # Calculate total cost/proceeds
            total_amount = quantity * price
            print(f"Total amount: ${total_amount:,.2f}")
            
            # For sells, make quantity negative
            if trade_type == "SELL":
                quantity = -quantity
                
            # Check if player has enough cash for buy
            if trade_type == "BUY" and total_amount > player.cash_balance:
                print(f"Error: Insufficient funds. Required: ${total_amount:,.2f}, Available: ${player.cash_balance:,.2f}")
                return None
                
            # Create and record the trade
            now = datetime.utcnow()
            trade = Trade(
                player_id=player_id,
                ticker=ticker.upper(),
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                type=trade_type,
                trade_date=trade_date,  # Use provided trade_date
                created_at=now  # Keep created_at as current time
            )
            
            print(f"Current cash balance: ${player.cash_balance:,.2f}")
            # Update player's cash balance
            if trade_type == "BUY":
                player.cash_balance -= total_amount
            else:
                player.cash_balance += total_amount
            print(f"New cash balance: ${player.cash_balance:,.2f}")
                
            # Update or create position
            position = self.update_position(player_id, ticker, trade_type, abs(quantity), price)
            if position:
                print(f"Updated position - Ticker: {position.ticker}, Quantity: {position.quantity}, Avg Price: ${position.average_price:,.2f}")
            
            # Save changes
            self.db.add(trade)
            self.db.commit()
            print("Trade processed successfully")
            
            return trade
            
        except Exception as e:
            print(f"Error processing trade: {str(e)}")
            import traceback
            print(traceback.format_exc())
            self.db.rollback()
            return None

    def check_contest_completion(self, contest_id: int) -> bool:
        """Check if contest should be completed based on win condition."""
        # For now, we'll leave this as a manual process
        # In the future, we can add logic to parse and evaluate win conditions
        return False

    def end_contest(self, contest_id: int, winner_id: int) -> bool:
        """End a contest and set the winner."""
        # Removed since contests should persist after payout
        return True
        
    def payout_winner(self, contest_id: int, winner_id: int) -> bool:
        """Process payout to contest winner using Payman."""
        try:
            print(f"Starting payout process for contest {contest_id}, winner {winner_id}")
            from app import payman
            
            print("Creating agent payee...")
            # Create agent payee
            winner_agent_payee = payman.payments.create_payee(
                type='PAYMAN_AGENT',
                payman_agent='agt-1efec0ba-aca9-66db-9c15-ed3e511002ed',
                name='Contest Winner',
                contact_details={
                    'email': 'marc@a16z.com'
                }
            )
            print(f"Agent payee created: {winner_agent_payee}")
            
            print("Sending payment...")
            # Send payment
            payment = payman.payments.send_payment(
                amount_decimal=50.00,
                payment_destination_id=winner_agent_payee.id,
                memo='Contest winnings payment'
            )
            
            print('Payment sent:', payment.reference)
            return True
            
        except Exception as e:
            print(f"Payman error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
