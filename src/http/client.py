import logging
import os
from typing import Literal

import requests

from src.wallet import Wallet


class HttpJsonClient:
	def __init__(self, url):
		self.url = url

	def request(self, method: Literal["get", "post"], endpoint: str, json: dict = None, params: dict = None) -> dict or list:
		try:
			response = requests.request(method, f'{self.url}/{endpoint}', params=params, json=json)
			if response.ok:
				return response.json()
			else:
				logging.error(f'Error while HTTP request (code: {response.status_code}, content: {response.content}')
		except requests.exceptions.ConnectionError:
			logging.error(f"Can't connect to node {self.url}")

	def get(self, endpoint: str, **kwargs):
		return self.request('get', endpoint, **kwargs)

	def post(self, endpoint: str, **kwargs):
		return self.request('post', endpoint, **kwargs)

	def get_chain(self):
		return self.get('chain')

	def create_transaction(
			self, amount: str, fee: str, recipient: str,
			sender: str = None, private_key: str = None, public_key: str = None,
	) -> dict:
		wallet = Wallet(
			address=sender if sender else os.getenv('ADDRESS'),
			private_key=private_key if private_key else os.getenv('PRIVATE_KEY'),
			public_key=public_key if public_key else os.getenv('PUBLIC_KEY')
		)
		transaction = wallet.create_transaction(amount=amount, fee=fee, recipient=recipient)
		return self.post('send', json={
			'public_key': transaction.public_key,
			'signature': transaction.signature,
			'amount': transaction.raw.amount,
			'fee': transaction.raw.fee,
			'sender': transaction.raw.sender,
			'recipient': transaction.raw.recipient,
			'timestamp': transaction.raw.timestamp
		})
