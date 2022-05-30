import logging
from time import time, sleep
from typing import Tuple

from src import HttpJsonClient, Blockchain
import itertools


def is_all_nodes_reached_required_len(wallets: Tuple[HttpJsonClient, ...], chain_len: int):
	start = time()
	finished = [False for _ in wallets]
	while Blockchain.threshold_block_time * chain_len > time() - start and not all(finished):
		for index, wallet in enumerate(wallets):
			chain = wallet.get_chain()
			if not chain:
				continue
			if chain['len'] < chain_len or len(chain['blocks']) < chain_len:
				logging.info(f'Chain {wallet.url} not reached ({chain["len"]}) required length {chain_len}')
			else:
				logging.info(f'Chain {wallet.url} now ready ({chain["len"]})')
				finished[index] = True
			sleep(1)
	return all(finished)


def is_all_nodes_blocks_equals(wallets: Tuple[HttpJsonClient, ...], chain_len: int):
	chains = [wallet.get_chain()['blocks'][:chain_len] for wallet in wallets]
	return chains.count(chains[0]) == len(chains)


def is_transaction_in_chain(chain: dict, amount: str, fee: str, recipient: str, lock_script: str):
	transactions = list(
		itertools.chain.from_iterable(
			[block['transactions'] for block in chain['blocks']]
		)
	)
	return [
		transaction for transaction in transactions
		if transaction['raw']['recipient'] == recipient
		   and transaction['raw']['amount'] == amount
		   and transaction['raw']['fee'] == fee
		   and transaction['raw']['lock_script'] == lock_script
	]
