from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum

Base = declarative_base()

class ContestStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Contest(Base):
    __tablename__ = 'contests'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    join_code = Column(String, unique=True, nullable=False)
    win_condition = Column(String, nullable=False)
    starting_balance = Column(Float, nullable=False, default=10000.0)  # Default $10k starting balance
    status = Column(Enum(ContestStatus), default=ContestStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    players = relationship("Player", back_populates="contest")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contest_id = Column(Integer, ForeignKey('contests.id'))
    starting_balance = Column(Float, nullable=False)  # Set when joining contest
    cash_balance = Column(Float, nullable=False)     # Available cash
    created_at = Column(DateTime, default=datetime.utcnow)
    contest = relationship("Contest", back_populates="players")
    trades = relationship("Trade", back_populates="player")
    positions = relationship("Position", back_populates="player")

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)  # Updated when viewing leaderboard
    last_updated = Column(DateTime, default=datetime.utcnow)
    player = relationship("Player", back_populates="positions")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # 'BUY' or 'SELL'
    total_amount = Column(Float, nullable=False)  # quantity * price
    trade_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    player = relationship("Player", back_populates="trades")

def init_db(db_path='trading_contest.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
