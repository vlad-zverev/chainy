import hashlib
import json
from copy import deepcopy
from decimal import Decimal
from typing import List

from src.db.connector import DatabaseConnector
from src.db.models import BlockModel
from src.utils import actual_time, serialize


class AttrsAsHash:
	@property
	def hash(self) -> str:
		return hashlib.sha256(
			json.dumps(
				self.__dict__, sort_keys=True, default=serialize
			).encode()
		).hexdigest()


class RawTransaction:
	def __init__(self, amount: str, fee: str, sender: str, recipient: str, timestamp: int = None):
		self.amount = amount
		self.sender = sender
		self.recipient = recipient
		self.fee = fee
		self.timestamp = timestamp if timestamp else actual_time()

	@property
	def hash(self) -> str:
		return hashlib.sha256(
			json.dumps(
				self.__dict__, sort_keys=True, default=serialize
			).encode()
		).hexdigest()


class Transaction:
	def __init__(self, signature: str, public_key: str, raw: RawTransaction):
		self.signature = signature
		self.public_key = public_key
		self.raw = raw

	@property
	def header(self):
		header = deepcopy(self.__dict__)
		del header['raw']
		return header

	@property
	def hash(self) -> str:
		return hashlib.sha256(
			json.dumps(
				{
					'signature': self.signature,
					'public_key': self.public_key,
					'amount': self.raw.amount,
					'fee': self.raw.fee,
					'sender': self.raw.sender,
					'recipient': self.raw.recipient,
					'timestamp': self.raw.timestamp,
				}, sort_keys=True, default=serialize
			).encode()
		).hexdigest()


class Block:
	MAX_SIZE = 100

	def __init__(
			self, index: int,
			transactions: List[Transaction],
			timestamp: int,
			previous_hash: str,
			nonce: int = 0,
	):
		self.transactions = transactions

		self.index = index
		self.timestamp = timestamp
		self.previous_hash = previous_hash
		self.nonce = nonce

	@property
	def info(self):
		return {**self.__dict__, **{'hash': self.hash}}

	@property
	def hash(self) -> str:
		return hashlib.sha256(
			json.dumps(
				{
					'index': self.index,
					'timestamp': self.timestamp,
					'previous_hash': self.previous_hash,
					'nonce': self.nonce,
				}, sort_keys=True, default=serialize
			).encode()
		).hexdigest()

	@property
	def header(self):
		header = self.info
		del header['transactions']
		return header


class Blockchain:
	difficulty = 5
	threshold_block_time = 10_000_000  # 10 sec
	total_emission = Decimal(1_000_000)
	block_reward = Decimal(1)

	def __init__(self):
		self.unconfirmed_transactions: List[Transaction] = []
		self.chain: List[Block] = []
		self.db: DatabaseConnector or None = None

	def __len__(self):
		return len(self.chain)

	def __add__(self, block: Block):
		self.chain.append(block)
		if self.db:
			self.db.save_block_with_transactions(block)

	@property
	def blocks(self):
		self.update_local_chain()
		return self.chain

	def update_local_chain(self):
		chain = []
		db_blocks = self.db.get_all(BlockModel)
		for db_block in db_blocks:
			chain.append(Block(
				index=db_block.index,
				transactions=[
					Transaction(
						signature=tx.signature,
						public_key=tx.public_key,
						raw=RawTransaction(
							amount=tx.amount,
							fee=tx.fee,
							sender=tx.sender,
							recipient=tx.recipient,
							timestamp=tx.timestamp,
						)
					) for tx in db_block.transactions
				],
				timestamp=db_block.timestamp,
				previous_hash=db_block.previous_hash,
				nonce=db_block.nonce,
			))
		self.chain = chain

	def create_initial_block(self) -> Block:
		block = Block(
			index=0,
			transactions=[self._create_initial_transaction()],
			timestamp=actual_time(),
			previous_hash='0',
		)
		self + block
		return block

	def _create_initial_transaction(self) -> Transaction:
		raw_transaction = RawTransaction(
			amount=str(self.total_emission),
			fee='0',
			sender='0',
			recipient='root',
		)
		return Transaction(
			signature='0',
			public_key='0',
			raw=raw_transaction,
		)

	def pay_fee(self, recipient: str):
		raw_transaction = RawTransaction(
			amount=str(self.block_reward),
			fee='0',
			sender='root',
			recipient=recipient,
		)
		return Transaction(
			signature='0',
			public_key='0',
			raw=raw_transaction,
		)

	@property
	def last_block(self) -> Block:
		return self.chain[-1]

	def edit_difficulty(self) -> None:
		is_long_calculation = (actual_time() - self.last_block.timestamp) < self.threshold_block_time
		self.difficulty += (-1, 1)[int(is_long_calculation)]

	@staticmethod
	def get_hash(block: dict) -> str:
		return hashlib.sha256(
			json.dumps(block).encode()
		).hexdigest()
