from src.chain import Blockchain, Transaction
from src.http.server import start, app
from src.miner import Miner
from src.utils import get_env_var
from src.wallet import Wallet
from src.http.client import HttpJsonClient

miner = Miner(Blockchain())

PORT = get_env_var('PORT', default=5000)
client = HttpJsonClient(F'http://127.0.0.1:{PORT}')
MODULE = get_env_var('MODULE', default='wallet')
DEBUG = bool(get_env_var('DEBUG', 1))


modules = {
	'miner': (miner.main, {}),
	'wallet': (start, {'debug': DEBUG, 'port': PORT, 'node': miner, 'server': app}),
	'client': (client.create_transaction, {'amount': '0.5', 'fee': '1', 'recipient': 'test'}),
}

app, args = modules[MODULE]
app(**args)
