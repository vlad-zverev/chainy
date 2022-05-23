import hashlib
import json
import logging
import time
import traceback
from decimal import Decimal
from typing import List

import base58
import ecdsa
from ecdsa.keys import BadSignatureError, MalformedPointError

from src.utils import actual_time, serialize


class RawTransaction:
    def __init__(self, amount: Decimal, fee: Decimal, sender: str, receiver: str):
        self.amount = amount
        self.sender = sender
        self.receiver = receiver
        self.fee = fee
        self.timestamp = actual_time()

    def hash(self):
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()


class Transaction:
    def __init__(self, signature: str, message: str, public_key: str, raw: RawTransaction):
        self.public_key = public_key
        self.signature = signature
        self.message = message
        self.raw = raw


class Block:
    MAX_SIZE = 100

    def __init__(
            self, index: int,
            transactions: List[Transaction],
            timestamp: int,
            previous_hash: str,
            nonce: int = 0,
    ):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = None

    def compute_hash(self) -> str:
        block_string = json.dumps(self.__dict__, sort_keys=True, default=serialize)
        return hashlib.sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 4
    threshold_block_time = 10_000_000  # 10 sec

    def __init__(self):
        self.unconfirmed_transactions: List[Transaction] = []
        self.chain: List[Block] = []

        self._create_initial_block()

    def _create_initial_block(self) -> Block:
        block = Block(
            index=0,
            transactions=[],
            timestamp=actual_time(),
            previous_hash='0',
        )
        block.hash = block.compute_hash()
        self.chain.append(block)
        return block

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def proof_of_work(self, block: Block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        logging.info(f'PoW completed after {block.nonce} iterations')
        return computed_hash

    def is_valid_proof(self, block, block_hash):
        return block_hash.startswith('0' * self.difficulty) and block_hash == block.compute_hash()

    def add_block(self, block: Block, proof: str):
        if self.last_block.hash != block.previous_hash:
            return False
        if not self.is_valid_proof(block, proof):
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def edit_difficulty(self):
        is_long_calculation = (actual_time() - self.last_block.timestamp) < self.threshold_block_time
        self.difficulty += (-1, 1)[int(is_long_calculation)]


class Miner:
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def add_new_transaction(self, transaction: Transaction):
        self.validate_signature(transaction.public_key, transaction.signature, transaction.message)
        self.blockchain.unconfirmed_transactions.append(transaction)

    def mine(self):
        if not self.blockchain.unconfirmed_transactions:
            logging.info('Nothing to mine...')
            return
        last_block = self.blockchain.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.blockchain.unconfirmed_transactions,
            timestamp=int(time.time() * 1_000_000),
            previous_hash=last_block.hash,
        )
        proof = self.blockchain.proof_of_work(new_block)
        self.blockchain.add_block(new_block, proof)
        self.blockchain.unconfirmed_transactions = []
        return new_block

    @staticmethod
    def validate_signature(public_key: str, signature: str, message: str) -> bool:
        signature = base58.b58decode(signature)
        try:
            verifying_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
            return verifying_key.verify(signature, message.encode())
        except (BadSignatureError, MalformedPointError) as e:
            logging.error(f'Invalid operation: {e}, {traceback.format_exc()}')
            return False
