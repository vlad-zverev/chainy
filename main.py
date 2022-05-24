from src.chain import Blockchain
from src.http.server import start, app
from src.miner import Miner
from src.utils import get_env_var

miner = Miner(Blockchain())

PORT = get_env_var('PORT', default=5000)
MODULE = get_env_var('MODULE', default='wallet')
DEBUG = bool(get_env_var('DEBUG', 1))

modules = {
	'miner': (miner.main, {}),
	'wallet': (start, {'debug': DEBUG, 'port': PORT, 'node': miner, 'server': app}),
}

app, args = modules[MODULE]
app(**args)
