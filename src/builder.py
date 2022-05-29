import atexit
import logging
import threading
from typing import List

from flask import Flask

from src.chain import Blockchain
from src.miner import Miner


class AppBuilder:
	def __init__(self, nodes: List[str] = None):
		self.flask = Flask(self.__module__)
		self._lock = threading.Lock()
		self.miner = Miner(Blockchain())
		self.nodes = nodes
		atexit.register(self.exit)

		self.start_mining()

	@staticmethod
	def exit():
		logging.info('Interrupted...')

	def mine(self):
		with self._lock:
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
