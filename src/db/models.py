from sqlalchemy import (
	Column, Integer, String,
	ForeignKeyConstraint, Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BlockModel(Base):
	__tablename__ = 'blocks'

	index = Column(Integer, nullable=False, primary_key=True)
	timestamp = Column(Integer, nullable=False)
	hash = Column(String(64), nullable=False, unique=True, index=True)
	previous_hash = Column(String(64), nullable=False, unique=True)
	nonce = Column(Integer, nullable=False)

	transactions = relationship('TransactionModel', back_populates='block')


class TransactionModel(Base):
	__tablename__ = 'transactions'

	amount = Column(String, nullable=False)
	fee = Column(String, nullable=False)
	sender = Column(String(64))
	recipient = Column(String(64))
	timestamp = Column(Integer, nullable=False)

	id = Column(Integer, primary_key=True)
	signature = Column(String(64))
	public_key = Column(String(64))
	hash = Column(String(64), index=True)
	lock_script = Column(Text, default=None)

	block_index = Column(Integer)

	block = relationship('BlockModel', back_populates='transactions')

	__table_args__ = (
		ForeignKeyConstraint(('block_index',), ('blocks.index',)),
	)


class UserRequest(Base):
	__tablename__ = 'users_requests'

	id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)
	request = Column(String, nullable=False)
	checked = Column(Integer, default=0, index=True)
