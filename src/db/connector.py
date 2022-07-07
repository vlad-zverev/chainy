import json
import logging
import os
import traceback
from typing import List
from contextlib import contextmanager
from copy import deepcopy

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import scoped_session, sessionmaker

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
        finally:
            db.recreate_session()
        return result

    return wrapped


class DatabaseConnector:

    def __init__(self, drop_and_create: bool = False, debug: bool = False):
        self.engine = create_engine(
            url=f'sqlite:///{os.getenv("ADDRESS")}.sqlite',
            connect_args={'check_same_thread': False, 'timeout': 15},
            echo=debug
        )
        self.engine.connect()
        self.metadata = Base.metadata
        if drop_and_create:
            self.recreate_tables()

    @contextmanager
    def session(self):
        Session = scoped_session(sessionmaker(bind=self.engine, autoflush=False))
        session = Session()
        yield session
        self.commit(session)
        Session.remove()

    @staticmethod
    def commit(session):
        try:
            session.commit()
        except IntegrityError:
            session.rollback()

    def recreate_tables(self):
        self.drop_all_tables()
        self.create_all_tables()

    def create_all_tables(self):
        self.metadata.create_all(self.engine)

    def drop_all_tables(self):
        self.metadata.drop_all(self.engine)

    @staticmethod
    def add(session, entity: Base, flush: bool = True) -> Base:
        session.add(instance=entity)
        if flush:
            try:
                session.flush()
            except IntegrityError:
                logging.error(traceback.format_exc())
                session.rollback()
        return entity

    @staticmethod
    def query(session, *entities):
        return session.query(*entities)

    def get_all(self, session, *entities) -> List[BlockModel]:
        return self.query(session, *entities).all()

    def _add_block(self, session, **kwargs) -> BlockModel:
        return self.add(session, BlockModel(**kwargs))

    def _add_transaction(self, session, **kwargs) -> TransactionModel:
        return self.add(session, TransactionModel(**kwargs))

    def save_user_request(self, request):
        with self.session() as session:
            return self.add(session, UserRequest(request=json.dumps(request)))

    def save_block_with_transactions(self, block):
        with self.session() as session:
            self._add_block(session, **block.header)
            for transaction in block.transactions:
                self._add_transaction(
                    session, **{
                        **transaction.header,
                        **transaction.raw.__dict__,
                        'block_index': block.index,
                        'hash': transaction.hash,
                    })

    def replace_chain(self, chain: dict):
        with self.session() as session:
            self.query(session, BlockModel).delete()
            self.query(session, TransactionModel).delete()
            for block in chain['blocks']:
                db_block = deepcopy(block)
                del db_block['transactions']
                self._add_block(session, **db_block)
                for transaction in block['transactions']:
                    self._add_transaction(
                        session, **{
                            'signature': transaction['signature'],
                            'public_key': transaction['public_key'],
                            'sender': transaction['raw']['sender'],
                            'recipient': transaction['raw']['recipient'],
                            'amount': transaction['raw']['amount'],
                            'fee': transaction['raw']['fee'],
                            'lock_script': transaction['raw']['lock_script'],
                            'timestamp': transaction['raw']['timestamp'],
                            'hash': '0',
                            'block_index': block['index'],
                    })

    def replace_local_chain(self, Transaction, RawTransaction, Block):
        chain = []
        with self.session() as session:
            db_blocks = self.get_all(session, BlockModel)
            logging.info(f'Blocks updating: {len(db_blocks)}')
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
                                lock_script=tx.lock_script,
                            )
                        ) for tx in db_block.transactions
                    ],
                    timestamp=db_block.timestamp,
                    previous_hash=db_block.previous_hash,
                    nonce=db_block.nonce,
                ))
            return chain

    def get_unseen_requests(self):
        with self.session() as session:
            return self.query(session, UserRequest).filter(~UserRequest.checked)

    def mark_requests_as_viewed(self, data):
        with self.session() as session:
            self.query(session, UserRequest).filter(UserRequest.id == data.id).update({UserRequest.checked: 1})
