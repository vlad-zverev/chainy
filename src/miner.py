import hashlib
import json
import logging
import os
import sys
import traceback
from time import sleep
from typing import List

import base58
import ecdsa
from ecdsa.keys import BadSignatureError, MalformedPointError

from src.chain import Blockchain, Block, Transaction
from src.http.client import HttpJsonClient
from src.db.connector import DatabaseConnector
from src.utils import actual_time
from src.wallet import Wallet

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=f"%(asctime)s - [%(levelname)s] - %(message)s")

NODES = os.getenv('NODES')


class Miner:
    def __init__(self, blockchain: Blockchain, greedy_mode: bool = True):
        self.address = os.getenv('ADDRESS') if os.getenv('ADDRESS') else Wallet().address

        self.blockchain = blockchain
        self.blockchain.db = DatabaseConnector(f'{self.address}')
        if not len(self.blockchain):
            self.blockchain.create_initial_block()

        self.greedy_mode = greedy_mode
        self.nodes: List[str] = NODES if NODES else []

    def mine(self) -> Block or None:
        last_block = self.blockchain.last_block
        self.blockchain.unconfirmed_transactions.append(self.blockchain.pay_fee(self.address))
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.blockchain.unconfirmed_transactions,
            timestamp=actual_time(),
            previous_hash=last_block.hash,
        )
        self.proof_of_work(new_block)
        self.add_block(new_block)
        self.blockchain.unconfirmed_transactions = []
        return new_block

    @staticmethod
    def get_hash(block: dict) -> str:
        return hashlib.sha256(
            json.dumps(block).encode()
        ).hexdigest()

    def proof_of_work(self, block: Block) -> None:
        block.nonce = 0
        while not self.is_valid_proof(block.hash):
            block.nonce += 1
        logging.info(f'PoW completed after {block.nonce} iterations')

    def is_valid_proof(self, proof: str) -> bool:
        return proof.startswith('0' * self.blockchain.difficulty)

    def add_block(self, block: Block) -> None:
        if self.blockchain.last_block.hash != block.previous_hash:
            raise
        if not self.is_valid_proof(block.hash):
            raise
        self.blockchain + block

    def validate(self, transaction: Transaction) -> bool:
        return self.validate_signature(transaction.public_key, transaction.signature, transaction.raw.hash) \
               and self.validate_balance(transaction)

    def add_new_transaction(self, transaction: Transaction) -> None:
        if self.validate(transaction):
            self.blockchain.unconfirmed_transactions.append(transaction)
        else:
            logging.info('Your transaction incorrect')

    @staticmethod
    def validate_signature(public_key: str, signature: str, message: str) -> bool:
        signature = base58.b58decode(signature)
        try:
            verifying_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
            return verifying_key.verify(signature, message.encode())
        except (BadSignatureError, MalformedPointError) as e:
            logging.error(f'Invalid operation: {e}, {traceback.format_exc()}')
            return False

    def validate_balance(self, transaction: Transaction) -> bool:
        required_amount = transaction.raw.amount + transaction.raw.fee
        wallet = Wallet(address=transaction.raw.sender)
        if wallet.is_balance_sufficient(self.blockchain, required_amount):
            return True

    def validate_node(self, blocks: List[dict]):
        for index, block in enumerate(blocks[1:]):
            previous_block = blocks[index-1]
            if block['previous_hash'] != self.get_hash(previous_block):
                return False
            if not self.is_valid_proof(block['hash']):
                return False
        return True

    def sync_nodes(self):
        for node in self.nodes:
            chain = HttpJsonClient(url=node).get_chain()
            if chain:
                if chain['len'] > len(self.blockchain) and self.validate_node(chain['blocks']):
                    self.blockchain.chain = chain['blocks']
                    logging.info('Chain replaced by another longer and valid chain')

    def mine_cycle(self):
        while True:
            self.blockchain.update_local_chain()
            self.mine()
            self.sync_nodes()
            sleep(1)

    def main(self):
        self.mine_cycle()
