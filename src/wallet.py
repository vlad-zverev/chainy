import binascii
import hashlib
import json
import logging
from copy import copy
from decimal import Decimal

import base58
import ecdsa

from src.miner import Blockchain, RawTransaction, Transaction
from src.utils import serialize


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
    def __init__(self, balance: Decimal = 0):
        crypto = Crypto()
        self.address = crypto.address
        self.balance = balance
        self.private_key = crypto.private
        self.public_key = crypto.public

    def is_sufficient(self, required_amount: Decimal = 0):
        if self.balance > required_amount:
            return True

    def get_balance(self, blockchain: Blockchain):
        balance = 0
        for block in blockchain.chain:
            for transaction in block.transactions:
                if transaction.raw.receiver == self.address:
                    balance += transaction.raw.amount
                if transaction.raw.sender == self.address:
                    balance -= transaction.raw.amount - transaction.raw.fee
        return balance

    def sign_transaction(self, transaction: RawTransaction):
        message = json.dumps(transaction.__dict__, default=serialize)
        bytes_message = message.encode()
        signing_key = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
        signature = base58.b58encode(signing_key.sign(bytes_message))
        return signature, message

    def create_transaction(self, amount: str, fee: str, receiver: str):
        raw_transaction = RawTransaction(
            amount=Decimal(amount),
            fee=Decimal(fee),
            sender=self.address,
            receiver=receiver,
        )
        return Transaction(
            *self.sign_transaction(raw_transaction),
            public_key=self.public_key,
            raw=raw_transaction,
        )
