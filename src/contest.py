from datetime import datetime
import random
import string
from typing import List, Optional
from sqlalchemy.orm import Session
from database import Contest, Player, Trade, ContestStatus

def generate_join_code(length: int = 6) -> str:
    """Generate a random alphanumeric join code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class ContestManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_contest(self, name: str, target_profit: float) -> Contest:
        """Create a new contest with a unique join code."""
        join_code = generate_join_code()
        while self.db.query(Contest).filter_by(join_code=join_code).first():
            join_code = generate_join_code()

        contest = Contest(
            name=name,
            join_code=join_code,
            target_profit=target_profit,
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
            current_balance=0.0,
            unrealized_profit=0.0
        )
        self.db.add(player)
        self.db.commit()
        return player

    def get_leaderboard(self, contest_id: int) -> List[dict]:
        """Get the current leaderboard for a contest."""
        players = self.db.query(Player).filter_by(contest_id=contest_id).all()
        leaderboard = [
            {
                "name": player.name,
                "balance": player.current_balance,
                "unrealized_profit": player.unrealized_profit,
                "total_profit": player.current_balance + player.unrealized_profit
            }
            for player in players
        ]
        return sorted(leaderboard, key=lambda x: x["total_profit"], reverse=True)

    def check_contest_completion(self, contest_id: int) -> bool:
        """Check if any player has reached the target profit."""
        contest = self.db.query(Contest).filter_by(id=contest_id).first()
        if not contest or contest.status != ContestStatus.ACTIVE:
            return False

        for player in contest.players:
            total_profit = player.current_balance + player.unrealized_profit
            if total_profit >= contest.target_profit:
                contest.status = ContestStatus.COMPLETED
                self.db.commit()
                return True
        return False

    def record_trade(self, player_id: int, trade_data: dict) -> Optional[Trade]:
        """Record a new trade for a player."""
        player = self.db.query(Player).filter_by(id=player_id).first()
        if not player:
            return None

        trade = Trade(
            player_id=player_id,
            ticker=trade_data["ticker"],
            quantity=trade_data["quantity"],
            price=trade_data["price"],
            type=trade_data["trade_type"],
            screenshot_path=trade_data.get("screenshot_path"),
            trade_date=trade_data.get("date", datetime.utcnow())
        )
        self.db.add(trade)
        self.db.commit()
        return trade
