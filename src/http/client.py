import requests
from typing import Literal
import logging


class HttpJsonClient:
	def __init__(self, url):
		self.url = url

	def request(self, method: Literal["get", "post"], endpoint: str, json: dict = None, params: dict = None) -> dict or list:
		response = requests.request(method, f'{self.url}/{endpoint}', params=params, json=json)
		if response.ok:
			return response.json()
		else:
			logging.error(f'Error while HTTP request (code: {response.status_code}, content: {response.content}')

	def get(self, endpoint: str, **kwargs):
		return self.request('get', endpoint, **kwargs)

	def post(self, endpoint: str, **kwargs):
		return self.request('post', endpoint, **kwargs)

	def get_chain(self):
		return self.get('chain')
