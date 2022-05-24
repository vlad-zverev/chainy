from sqlalchemy import (
	Column, Integer, String,
	Numeric, ForeignKeyConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
	sender = Column(String(128))
	recipient = Column(String(128))
	timestamp = Column(Integer, nullable=False)

	signature = Column(String(128))
	public_key = Column(String(128))
	hash = Column(String(128), unique=True, index=True, primary_key=True)
	block_index = Column(Integer)

	block = relationship('BlockModel')

	__table_args__ = (
		ForeignKeyConstraint(('block_index',), ('blocks.index',)),
	)
