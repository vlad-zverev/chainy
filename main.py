from src.chain import Blockchain, Transaction
from src.http.server import start, app
from src.miner import Miner
from src.utils import get_env_var
from src.wallet import Wallet
from src.db.models import engine
from src.http.client import HttpJsonClient

miner = Miner(Blockchain(), engine)

client = HttpJsonClient('http://127.0.0.1:5000')
PORT = get_env_var('PORT', default=5000)
MODULE = get_env_var('MODULE', default='wallet')
DEBUG = bool(get_env_var('DEBUG', 1))

wallet = Wallet(
	address='1Bj7zUHSDfZu3aBokesoeaY9HGtomnefGp',
	private_key='23d2d28749199b1cf6978ff3dcaee80709c1a45bcb855b8c7cbd15aecfb47e29',
	public_key='04d379ab5f5c382ae70ae572f6aaaa0f1cab6d84b1a936a95c66c6a8392ccbd7714c965e4894b18e9dbd023a2bb1b1c3b7a56e4997adfcc7e8a963cd754f78ed19'
)

transaction = wallet.create_transaction(amount='3', fee='1', recipient='test')
print(transaction.signature)
tx = {
	'public_key': transaction.public_key,
	'signature': transaction.signature,
	'amount': transaction.raw.amount,
	'fee': transaction.raw.fee,
	'sender': transaction.raw.sender,
	'recipient': transaction.raw.recipient,
	'timestamp': transaction.raw.timestamp
}

modules = {
	'miner': (miner.main, {}),
	'wallet': (start, {'debug': DEBUG, 'port': PORT, 'node': miner, 'server': app}),
	'client': (client.post, {'endpoint': 'send', 'json': tx}),
}

app, args = modules[MODULE]
app(**args)
