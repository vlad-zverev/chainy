import binascii
import hashlib
import logging
from copy import copy
from decimal import Decimal
import time
import base58
import ecdsa

from src.chain import Blockchain, RawTransaction, Transaction


class Crypto:
    def __init__(self):
        ecdsa_private = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.private = ecdsa_private.to_string().hex()
        self.public = '04' + ecdsa_private.get_verifying_key().to_string().hex()
        self.address = self.generate_address()

    def generate_address(self):
        public_sha256 = hashlib.sha256(binascii.unhexlify(self.public)).hexdigest()
        public_ridemp160 = hashlib.new('ripemd160', binascii.unhexlify(public_sha256))
        public_with_bytes = '00' + public_ridemp160.hexdigest()
        public_with_checksum = public_with_bytes + self.checksum(public_with_bytes)
        return base58.b58encode(binascii.unhexlify(public_with_checksum)).decode()

    @staticmethod
    def checksum(with_bytes_public):
        hash_ = copy(with_bytes_public)
        for _ in range(2):
            hash_ = hashlib.sha256(binascii.unhexlify(hash_)).hexdigest()
        return hash_[:8]


class Wallet:
    trust_confirmations = 3

    def __init__(
            self,
            address: str = None,
            private_key: str = None,
            public_key: str = None,
    ):
        if not address:
            self._generate()
        else:
            self.address = address
            self.private_key = private_key
            self.public_key = public_key
        self.log()

    def log(self):
        logging.info(f'Address: {self.address}')
        logging.info(f'Private: {self.private_key}')
        logging.info(f'Public: {self.public_key}')

    def _generate(self):
        crypto = Crypto()
        self.address = crypto.address
        self.private_key = crypto.private
        self.public_key = crypto.public

    def is_balance_sufficient(self, blockchain: Blockchain, required_amount: Decimal = 0):
        balance, _, _, _ = self.get_balance(blockchain)
        if balance >= Decimal(required_amount):
            return True
        else:
            logging.warning(f'Insufficient balance {balance}, required {required_amount}')

    def get_transaction_balance(self, transaction: Transaction, balance: Decimal, locked_balance: Decimal):
        if transaction.raw.recipient == self.address:
            balance += Decimal(transaction.raw.amount)
            if transaction.raw.lock_script:
                local = {'time': time.time}
                exec(transaction.raw.lock_script, dict(), local)
                locked = local.get('locked')
                if locked:
                    logging.info(f'script locked amount {transaction.raw.amount} ({transaction.raw.lock_script})')
                    locked_balance += Decimal(transaction.raw.amount)
                    balance -= Decimal(transaction.raw.amount)
        if transaction.raw.sender == self.address:
            balance -= Decimal(transaction.raw.amount) - Decimal(transaction.raw.fee)
        return balance, locked_balance

    def get_balance(self, blockchain: Blockchain):
        balance = locked_balance = untrusted_balance = untrusted_locked_balance = Decimal(0)
        for index, block in enumerate(reversed(blockchain.chain)):
            for transaction in block.transactions:
                if index >= self.trust_confirmations:
                    balance, locked_balance = self.get_transaction_balance(transaction, balance, locked_balance)
                else:
                    untrusted_balance, untrusted_locked_balance = self.get_transaction_balance(
                        transaction, untrusted_balance, untrusted_locked_balance
                    )
        return balance, locked_balance, untrusted_balance, untrusted_locked_balance

    def sign_transaction(self, message: str):
        bytes_message = message.encode()
        signing_key = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
        return base58.b58encode(signing_key.sign(bytes_message)).decode()

    def create_transaction(self, amount: str, fee: str, recipient: str, lock_script: str):
        raw_transaction = RawTransaction(
            amount=amount,
            fee=fee,
            sender=self.address,
            recipient=recipient,
            lock_script=lock_script,
        )
        return Transaction(
            self.sign_transaction(raw_transaction.hash),
            public_key=self.public_key,
            raw=raw_transaction,
        )
