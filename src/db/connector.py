import json
import logging
import os
import traceback
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import *


def save(func):
	def wrapped(instance, *args, **kwargs):
		result = func(instance, *args, **kwargs)
		if hasattr(instance, 'session'):
			db = instance
		else:
			db = instance.db
		try:
			db.session.commit()
		except IntegrityError:
			db.session.rollback()
		return result
	return wrapped


class DatabaseConnector:

	def __init__(self, drop_and_create: bool = False, debug: bool = False):
		self.engine = create_engine(
			url=f'sqlite:///{os.getenv("ADDRESS")}.sqlite',
			connect_args={'check_same_thread': False},
			echo=debug
		)
		self.engine.connect()
		self.session = Session(bind=self.engine, autoflush=False)
		self.metadata = Base.metadata
		if drop_and_create:
			self.recreate_tables()

	@property
	def sync(self):
		return 'fetch'

	def recreate_tables(self):
		self.drop_all_tables()
		self.create_all_tables()

	def create_all_tables(self):
		self.metadata.create_all(self.engine)

	def drop_all_tables(self):
		self.metadata.drop_all(self.engine)

	def add(self, entity: Base, flush: bool = True) -> Base:
		self.session.add(instance=entity)
		if flush:
			try:
				self.session.flush()
			except IntegrityError:
				logging.error(traceback.format_exc())
				self.session.rollback()
		return entity

	def query(self, *entities):
		return self.session.query(*entities)

	def get_all(self, *entities) -> List[BlockModel]:
		return self.query(*entities).all()

	def add_block(self, **kwargs) -> BlockModel:
		return self.add(BlockModel(**kwargs))

	def add_transaction(self, **kwargs) -> TransactionModel:
		return self.add(TransactionModel(**kwargs))

	@save
	def save_user_request(self, request):
		return self.add(UserRequest(request=json.dumps(request)))

	@save
	def save_block_with_transactions(self, block):
		self.add_block(**block.header)
		for transaction in block.transactions:
			self.add_transaction(**{
				**transaction.header,
				**transaction.raw.__dict__,
				'block_index': block.index,
				'hash': transaction.hash,
			})
