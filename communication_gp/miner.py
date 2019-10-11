# Paste your version of miner.py from the clinet_mining_p
# folder here
import hashlib
import requests

import sys


# TODO: Implement functionality to search for a proof
def proof_of_work(last_block):
    block_string = json.dumps(last_block, sort_keys=True).encode()
    proof = 0
    while self.valid_proof(block_string, proof) is False:
        proof += 1
    return proof

def valid_proof(block_string, proof):
    guess = f'{block_string}{proof}'.encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:6] == '000000'

if __name__ == '__main__':
    # What node are we interacting with?
    if len(sys.argv) > 1:
        node = sys.argv[1]
    else:
        node = "http://localhost:5000"

    coins_mined = 0
    # Run forever until interrupted
    while True:
        # TODO: Get the last proof from the server and look for a new one
        res = requests.get(node + '/chain')
        json_response = json.load(content)
        chain = json_response['chain']
        last_block = chain[-1]

        proof = proof_of_work(last_block)

        # TODO: When found, POST it to the server {"proof": new_proof}
        # TODO: We're going to have to research how to do a POST in Python
        # HINT: Research `requests` and remember we're sending our data as JSON
        res = requests.post(url=node+'/mine', json={'proof': proof})
        post_response = json.loads(res)
        if post_response['message'] == 'New Block Forged':
            coins_mined += 1
            print(coins_mined)
        else:
            print(post_response)
        # TODO: If the server responds with 'New Block Forged'
        # add 1 to the number of coins mined and print it.  Otherwise,
        # print the message from the server.
