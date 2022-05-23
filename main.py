import json

from flask import Flask
from src.wallet import Wallet
from src.miner import Blockchain, Miner
import logging
from src.utils import serialize


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

blockchain = Blockchain()
miner = Miner(blockchain)
wallet = Wallet()
transaction = wallet.create_transaction(amount='123', fee='1', receiver='0x')
miner.add_new_transaction(transaction)
miner.mine()


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data}, default=serialize)


app.run(debug=True, port=5000)
