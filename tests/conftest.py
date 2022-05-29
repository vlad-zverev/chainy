import os

from pytest import fixture
from typing import Tuple

from src import HttpJsonClient


@fixture(scope='session')
def wallet_main() -> HttpJsonClient:
	return HttpJsonClient(os.getenv('WALLET_MAIN_URL'))


@fixture(scope='session')
def wallet_friendly() -> HttpJsonClient:
	return HttpJsonClient(os.getenv('WALLET_FRIENDLY_URL'))


@fixture(scope='session')
def wallet_hacker() -> HttpJsonClient:
	return HttpJsonClient(os.getenv('WALLET_HACKER_URL'))


@fixture(scope='session')
def wallets(
		wallet_main: HttpJsonClient,
		wallet_hacker: HttpJsonClient,
		wallet_friendly: HttpJsonClient,
) -> Tuple[HttpJsonClient, ...]:
	return wallet_main, wallet_hacker, wallet_friendly
