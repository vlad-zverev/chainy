import atexit
import logging
import threading
from typing import List

from flask import Flask

from src.chain import Blockchain
from src.miner import Miner
from src.wallet import Wallet


class AppBuilder:
	def __init__(self, nodes: List[str] = None, debug: bool = False):
		self.flask = Flask(self.__module__)
		self.wallet = Wallet
		self._lock = threading.Lock()
		self.miner = Miner(Blockchain(), debug=debug)
		self.nodes = nodes
		atexit.register(self.exit)

		self.start_mining()

	@staticmethod
	def exit():
		logging.info('Interrupted...')

	def mine(self):
		self.miner.main()

	def start_mining(self):
		thread = threading.Thread(daemon=True, target=self.mine)
		thread.start()

	def run(
			self, host: str = '0.0.0.0',
			port: int = 5000,
			debug: int or bool = False,
	):
		self.flask.run(host=host, port=port, debug=debug)
