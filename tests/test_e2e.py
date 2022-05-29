from pytest import mark

from matcher import *


@mark.parametrize('chain_len', [5])
def test_nodes_synchronized(wallets: Tuple[HttpJsonClient, ...], chain_len: int):
	assert is_all_nodes_reached_required_len(wallets, chain_len)
	assert is_all_nodes_blocks_equals(wallets, chain_len)
