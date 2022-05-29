from pytest import mark
from time import sleep
from matcher import *


@mark.parametrize('chain_len', [5])
def test_nodes_synchronized(wallets: Tuple[HttpJsonClient, ...], chain_len: int):
	assert is_all_nodes_reached_required_len(wallets, chain_len)
	assert is_all_nodes_blocks_equals(wallets, chain_len)


def test_transaction(wallet_main):
	wallet_main.create_transaction(amount='2', fee='1', recipient='test')
	sleep(10)
	transactions = [block['transactions'] for block in wallet_main.get_chain()['blocks']]
	assert [transaction for transaction in transactions
			if transaction['recipient'] == 'test'
			and transaction['amount'] == '2'
			and transaction['fee'] == '1']
