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
    target_profit = Column(Float, nullable=False)
    status = Column(Enum(ContestStatus), default=ContestStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    players = relationship("Player", back_populates="contest")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contest_id = Column(Integer, ForeignKey('contests.id'))
    current_balance = Column(Float, default=0.0)
    unrealized_profit = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    contest = relationship("Contest", back_populates="players")
    trades = relationship("Trade", back_populates="player")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # 'buy' or 'sell'
    screenshot_path = Column(String, nullable=True)
    trade_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    player = relationship("Player", back_populates="trades")

def init_db(db_path='trading_contest.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
