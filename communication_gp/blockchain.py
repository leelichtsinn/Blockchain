# Paste your version of blockchain.py from the client_mining_p
# folder here
# Paste your version of blockchain.py from the basic_block_gp
# folder here

import hashlib
import json
import requests
from time import time
from uuid import uuid4
import sys

from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.genesis_block()

    def genesis_block(self):

        block = {
            'index': 1,
            'timestamp': 0,
            'transactions': [],
            'proof': 99,
            'previous_hash': 1,
        }

        self.chain.append(block)


    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the Recipient
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the BLock that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """


        # json.dumps converts json into a string
        # hashlib.sha246 is used to createa hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.  It convertes the string to bytes.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        block_string = json.dumps(block, sort_keys=True).encode()

        # By itself, this function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string using hexadecimal characters, which is
        # easer to work with and understand.
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    # def proof_of_work(self):
    #     """
    #     Simple Proof of Work Algorithm
    #     Find a number p such that hash(last_block_string, p) contains 6 leading
    #     zeroes
    #     :return: A valid proof for the provided block
    #     """
    #     # TODO
    #     # turn the block into a block string, so that valid_proof can hash it
    #     block_string = json.dumps(self.last_block, sort_keys=True).encode()
    #     proof = 0
    #     # pass the block string and the proof to valid proof
    #     # untile we find a proof that works
    #     while self.valid_proof(block_string, proof) is False:
    #     # increment a proof
    #         proof += 1
    #     # return proof
    #     return proof

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 6
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        # TODO
        # hash the block string and proof together
        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # return True if that hash starts with 4 zeros, False otherwise
        return guess_hash[:6] == '000000'

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid.  We'll need this
        later when we are a part of a network.

        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        prev_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{prev_block}')
            print(f'{block}')
            print("\n-------------------\n")
            # Check that the hash of the block is correct
            # TODO: Return false if hash isn't correct

            # hash the previous block, and check that block.previous_hash matches it
            if self.hash(prev_block) != block['previous_hash']:
                return False

            # Check that the Proof of Work is correct
            # TODO: Return false if proof isn't correct
            block_string = json.dumps(prev_block, sort_keys=True)

            if not self.valid_proof(block_string, block['proof']):
                return False

            prev_block = block
            current_index += 1

        return True

    def broadcast_new_block(self, block):
        neighbors = self.nodes

        for neighbor in neighbors:
            res = requests.post(neighbor + '/block/new', json={'block': block})

            if res.status_code != 200:
                print('darn')

    def register_node(self, node):
        self.nodes.add(node)

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

# TODO: need to modify endpoint to receive and validate or reject a new proof sent by a client
@app.route('/mine', methods=['POST'])
def mine():
    values = request.get_json()

    new_proof = values['proof']

    block_string = json.dumps(blockchain.last_block, sort_keys=True)
    if blockchain.valid_proof(block_string, new_proof):
        blockchain.new_transaction(sender='0', recipient=node_identifier, amount=1)

        previous_hash = blockchain.hash(blockchain.last_block)
        block = blockchain.new_block(new_proof, previous_hash)

        blockchain.broadcast_new_block(block)

        # Send a response with the new block
        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    else:
        response = {
            'message': 'proof was invalid or already submitted'
        }
        return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        # TODO: Return the chain and its current length
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/valid-chain', methods=['GET'])
def full_chain():
    response = {
        'valid-chain': blockchain.valid_chain(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/last-block', methods=['GET'])
def full_chain():
    response = {
        'last-block': blockchain.last_block()
    }
    return jsonify(response), 200

#############Additional Code Added by our Colleagues################

@app.route('/block/new', methods=['POST'])
def new_block():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['block']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    received_block = values['block']
    old_block = blockchain.last_block

    # TODO: Check that the new block index is 1 higher than our last block
    if received_block['index'] == old_block['index'] + 1:
        #that the hashes match
        if received_block['previous_hash'] == blockchain.hash(old_block):
            block_string = json.dumps(old_block)
            if blockchain.valid_proof(block_string, received_block['proof']):
                print('we have a valid block')
                blockchain.chain.append(received_block)
                return 'Block accepted', 200
            else:
                return 'Block has invalid proof', 200
        else:
            return 'block hash does not match', 200
    else:
        longest_chain = len(blockchain.chain)
        for neighbor in self.nodes:
            response = requests.get(neighbor + '/chain')
            res = response.json()
            neighbor_chain = res['chain']
            if len(neighbor_chain) > len(longest_chain):
                longest_chain = neighbor_chain

        if longest_chain is not blockchain.chain:
            blockchain.chain = longest_chain

    return response, 200

    # TODO: Otherwise, check for consensus
    # Don't forget to send a response before asking for the full
    # chain from a server awaiting a response.

    return response, 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():

    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


# TODO: Get rid of the previous if __main__ and use this so we can change
# ports via the command line.  Note that this is not robust and will
# not catch errors
if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5000
    app.run(host='0.0.0.0', port=port)
