import os

from sqlalchemy import (
	Column, Integer, String,
	Numeric, ForeignKeyConstraint, Table, MetaData, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import os


engine = create_engine(f'sqlite:///{os.getenv("ADDRESS")}.sqlite', connect_args={'check_same_thread': False})
Base = declarative_base()


class BlockModel(Base):
	__tablename__ = 'blocks'

	index = Column(Integer, nullable=False, unique=True, primary_key=True)
	timestamp = Column(Integer, nullable=False)
	hash = Column(String(64), nullable=False, unique=True, index=True)
	previous_hash = Column(String(64), nullable=False, unique=True)
	nonce = Column(Integer, nullable=False)

	transactions = relationship('TransactionModel', backref='BlockModel')


class TransactionModel(Base):
	__tablename__ = 'transactions'

	amount = Column(Numeric, nullable=False)
	fee = Column(Numeric, nullable=False)
	sender = Column(String(64))
	recipient = Column(String(64))
	timestamp = Column(Integer, nullable=False)

	signature = Column(String(64))
	public_key = Column(String(64))
	hash = Column(String(64), unique=True, index=True, primary_key=True)
	block_index = Column(Integer)

	block = relationship('BlockModel')

	__table_args__ = (
		ForeignKeyConstraint(('block_index',), ('blocks.index',)),
	)


class UserRequest(Base):
	__tablename__ = 'users_requests'

	id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
	request = Column(String, nullable=False)
	checked = Column(Integer, default=0, index=True)
