import json
import os

from flask import request

from src.builder import AppBuilder
from src.http.client import HttpJsonClient
from src.utils import response

NODES = json.loads(os.getenv('NODES')) if os.getenv('NODES') else []

app = AppBuilder(nodes=NODES, debug=True)


@app.flask.route('/chain', methods=['GET'])
def chain():
    """ Get full chain """
    blocks = [block.info for block in app.miner.blockchain.blocks]
    return response({'len': len(blocks), 'blocks': blocks})


@app.flask.route('/send', methods=['POST'])
def send():
    """ User's request to create transaction (save to db and notify other nodes) """
    body = request.get_json()
    app.miner.blockchain.db.save_user_request(body)
    for node in app.nodes:
        HttpJsonClient(node).post('notify', json=body)
    return response({})


@app.flask.route('/notify', methods=['POST'])
def notify():
    app.miner.blockchain.db.save_user_request(request.get_json())
    return response({})
