import json

from flask import Flask, request

from src.chain import Blockchain
from src.miner import Miner
from src.wallet import Wallet
from src.utils import serialize, response
from src.db.models import UserRequest
import json
from src.http.client import HttpJsonClient
import os

app = Flask(__name__)
miner: Miner = None


NODES = json.loads(os.getenv('NODES')) if os.getenv('NODES') else []


@app.route('/chain', methods=['GET'])
def chain():
    blocks = [block.info for block in miner.blockchain.blocks]
    return response({'len': len(blocks), 'blocks': blocks})


@app.route('/send', methods=['POST'])
def send():
    body = request.get_json()
    miner.blockchain.db.save_user_request(body)
    for node in NODES:
        HttpJsonClient(node).post('notify', json=body)
    return response({})


@app.route('/notify', methods=['POST'])
def notify():
    miner.blockchain.db.save_user_request(request.get_json())
    return response({})


def start(server: Flask, node: Miner, debug: bool, port: int):
    global miner
    miner = node
    server.run(debug=debug, port=port)
