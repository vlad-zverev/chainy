from decimal import Decimal

from pytest import mark

from matcher import *


@mark.parametrize('chain_len', [5])
def test_nodes_synchronized(wallets: Tuple[HttpJsonClient, ...], chain_len: int):
	assert is_all_nodes_reached_required_len(wallets, chain_len)
	assert is_all_nodes_blocks_equals(wallets, chain_len)


@mark.parametrize('transaction', [{'amount': '0.5', 'fee': '0.1', 'recipient': 'test', 'lock_script': 'locked = True'}])
def test_transaction(wallet_main: HttpJsonClient, transaction: dict):
	while not Decimal(wallet_main.get_balance()['balance']) > Decimal(transaction['amount']) + Decimal(transaction['fee']):
		sleep(1)
	wallet_main.create_transaction(**transaction)
	sleep(10)
	assert is_transaction_in_chain(wallet_main.get_chain(), **transaction)
