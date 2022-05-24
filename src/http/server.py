import json

from flask import Flask, request

from src.chain import Blockchain
from src.miner import Miner
from src.wallet import Wallet
from src.utils import serialize

app = Flask(__name__)
miner: Miner = None


@app.route('/chain', methods=['GET'])
def get_chain():
    miner.blockchain.update_local_chain()
    blocks = [block.info for block in miner.blockchain.chain]
    return json.dumps({'length': len(blocks), 'blocks': blocks}, default=serialize)


@app.route('/chain', methods=['GET'])
def send():
    data = request.get_json()

    return json.dumps({}, default=serialize)


def start(server: Flask, node: Miner, debug: bool, port: int):
    global miner
    miner = node
    server.run(debug=debug, port=port)
