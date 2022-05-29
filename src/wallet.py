import binascii
import hashlib
import logging
from copy import copy
from decimal import Decimal

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
        balance = self.get_balance(blockchain)
        if balance >= Decimal(required_amount):
            return True
        else:
            logging.warning(f'Insufficient balance {balance}, required {required_amount}')

    def get_balance(self, blockchain: Blockchain):
        balance = 0
        for block in blockchain.chain:
            for transaction in block.transactions:
                if transaction.raw.recipient == self.address:
                    balance += Decimal(transaction.raw.amount)
                if transaction.raw.sender == self.address:
                    balance -= Decimal(transaction.raw.amount) - Decimal(transaction.raw.fee)
        return balance

    def sign_transaction(self, message: str):
        bytes_message = message.encode()
        signing_key = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
        return base58.b58encode(signing_key.sign(bytes_message)).decode()

    def create_transaction(self, amount: str, fee: str, recipient: str):
        raw_transaction = RawTransaction(
            amount=amount,
            fee=fee,
            sender=self.address,
            recipient=recipient,
        )
        return Transaction(
            self.sign_transaction(raw_transaction.hash),
            public_key=self.public_key,
            raw=raw_transaction,
        )
