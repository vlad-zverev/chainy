import json
import logging
import os
import sys
import time
import traceback
from decimal import Decimal
from typing import List, Tuple

import base58
import ecdsa
from ecdsa.keys import BadSignatureError, MalformedPointError

from src.chain import Blockchain, Block, Transaction, RawTransaction
from src.db.connector import DatabaseConnector
from src.http.client import HttpJsonClient
from src.utils import actual_time
from src.wallet import Wallet

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=f"%(asctime)s - [%(levelname)s] - %(message)s")


class Validator:
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

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
        required_amount = Decimal(transaction.raw.amount) + Decimal(transaction.raw.fee)
        wallet = Wallet(address=transaction.raw.sender)
        if wallet.is_balance_sufficient(self.blockchain, required_amount):
            return True

    def validate_node(self, blocks: List[dict]):
        for index, block in enumerate(blocks[1:]):
            previous_block = blocks[index]
            if block['previous_hash'] != previous_block['hash']:
                logging.warning(f"{block['previous_hash']} != {previous_block['hash']}")
                return False
            if not self.is_valid_proof(block['hash']):
                return False
        return True

    def is_valid_proof(self, proof: str) -> bool:
        return proof.startswith('0' * self.blockchain.difficulty)

    @staticmethod
    def validate_lock_script(code: str):
        if code:
            for string in 'import', 'subprocess':
                if string in code:
                    return False, f'"{string}" is not allowed'
            local = {'time': time.time}
            exec(code, dict(), local)
            locked = local.get('locked')
            if locked is None or not isinstance(locked, bool):
                logging.info(f'locked: {locked}')
                return False, 'lock_script must have assignment "locked = ...", where locked contain "bool" value'
        return True, 0


class Miner(Validator):
    def __init__(self, blockchain: Blockchain, debug: bool = False):
        super().__init__(blockchain)
        self.address = os.getenv('ADDRESS') if os.getenv('ADDRESS') else Wallet().address

        self.blockchain = blockchain
        self.blockchain.db = DatabaseConnector(drop_and_create=True, debug=debug)
        self.blockchain.update_local_chain()
        if not len(self.blockchain):
            self.blockchain.create_initial_block()

        self.nodes: List[str] = json.loads(os.getenv('NODES')) if os.getenv('NODES') else []

    def mine(self) -> Block or None:
        last_block = self.blockchain.last_block
        self.blockchain.unconfirmed_transactions.append(self.blockchain.pay_fee(self.address))
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.blockchain.unconfirmed_transactions,
            timestamp=actual_time(),
            previous_hash=last_block.hash,
        )
        if self.proof_of_work(new_block):
            self.add_block(new_block)
        self.blockchain.unconfirmed_transactions = []
        return new_block

    def proof_of_work(self, block: Block) -> bool:
        block.nonce = 0
        while not self.is_valid_proof(block.hash):
            if not block.nonce % 500_000:
                if self.sync_nodes():
                    return False
            block.nonce += 1
        logging.info(f'PoW completed after {block.nonce} iterations')
        return True

    def add_block(self, block: Block) -> None:
        if self.blockchain.last_block.hash != block.previous_hash:
            logging.error(f'{self.blockchain.last_block.hash} != {block.previous_hash}')
            raise
        if not self.is_valid_proof(block.hash):
            logging.error(f'Proof invalid {block.hash}')
            raise
        self.blockchain + block

    def validate(self, transaction: Transaction) -> Tuple[bool, str]:
        if not self.validate_signature(transaction.public_key, transaction.signature, transaction.raw.hash):
            return False, 'Incorrect signature'
        if not self.validate_balance(transaction):
            return False, 'Insufficient balance'
        lock_script_validated, message = self.validate_lock_script(transaction.raw.lock_script)
        if not lock_script_validated:
            return False, message
        return True, 'Validated'

    def add_new_transactions(self) -> None:
        required = ('signature', 'public_key', 'sender', 'recipient', 'amount', 'fee')
        for data in self.blockchain.db.get_unseen_requests():
            tx = json.loads(data.request)
            try:
                if not all(key in tx.keys() for key in required):
                    raise ValueError
                transaction = Transaction(
                    signature=tx['signature'],
                    public_key=tx['public_key'],
                    raw=RawTransaction(
                        amount=tx['amount'],
                        fee=tx['fee'],
                        sender=tx['sender'],
                        recipient=tx['recipient'],
                        timestamp=tx['timestamp'],
                        lock_script=tx['lock_script'],
                    )
                )
                validated, message = self.validate(transaction)
                if validated:
                    self.blockchain.unconfirmed_transactions.append(transaction)
                else:
                    logging.info(f'Your transaction incorrect, {message}')
            except (AttributeError, ValueError):
                logging.error(traceback.format_exc())
            finally:
                self.blockchain.db.mark_requests_as_viewed(data)

    def sync_nodes(self):
        logging.info('Nodes synchronization...')
        for node in self.nodes:
            chain = HttpJsonClient(url=node).get_chain()
            if chain:
                logging.info(f'{node} chain: {chain["len"]} blocks (our chain: {len(self.blockchain)})')
                if chain['len'] > len(self.blockchain) and self.validate_node(chain['blocks']):
                    self.blockchain.db.replace_chain(chain)
                    self.blockchain.update_local_chain()
                    logging.info('Chain replaced by another longer and valid chain')
                    return True


    def main(self):
        logging.info('Start mining...')
        while True:
            try:
                self.add_new_transactions()
                self.mine()
                self.sync_nodes()
            except BaseException as e:
                logging.error(f'Mining error: {e}, {traceback.format_exc()}')
