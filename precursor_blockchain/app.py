from flask import Flask, jsonify, request
from blockchain import Blockchain
import os # For checking if the blockchain data file exists

app = Flask(__name__)

# Initialize our blockchain.
# Try to load from file, otherwise create a new one.
blockchain_file = "blockchain_data.json"
precursor_chain = Blockchain()
if os.path.exists(blockchain_file):
    precursor_chain.load_chain(blockchain_file)
else:
    # Genesis block already created in __init__ if no file found
    pass # No explicit action needed here, it's handled by Blockchain() constructor

@app.route('/mine_block', methods=['GET'])
def mine_block_endpoint():
    """
    Mines a new block and adds it to the chain.
    This also includes all pending transactions.
    """
    if not precursor_chain.pending_transactions:
        response = {
            'message': 'No pending transactions to mine. Add some transactions first!'
        }
        return jsonify(response), 200

    new_block = precursor_chain.mine_block()
    precursor_chain.save_chain(blockchain_file) # Save after mining

    response = {
        'message': 'New Block Forged!',
        'index': new_block.index,
        'timestamp': str(new_block.timestamp),
        'transactions': new_block.transactions,
        'nonce': new_block.nonce,
        'hash': new_block.hash,
        'previous_hash': new_block.previous_hash,
    }
    return jsonify(response), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction_endpoint():
    """
    Adds a new transaction to the list of pending transactions.
    These will be included in the next mined block.
    """
    values = request.get_json()
    required = ['sender_urn', 'recipient_urn', 'chemical_urn', 'quantity', 'unit', 'event_type', 'details']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = precursor_chain.new_transaction(
        values['sender_urn'],
        values['recipient_urn'],
        values['chemical_urn'],
        values['quantity'],
        values['unit'],
        values['event_type'],
        values['details']
    )

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/get_chain', methods=['GET'])
def get_chain():
    """
    Returns the full blockchain.
    """
    chain_data = [block.to_dict() for block in precursor_chain.chain]
    response = {
        'chain': chain_data,
        'length': len(precursor_chain.chain)
    }
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid_endpoint():
    """
    Checks if the entire blockchain is valid (no tampering, correct PoW).
    """
    is_valid = precursor_chain.is_chain_valid()
    if is_valid:
        response = {'message': 'The blockchain is valid.'}
    else:
        response = {'message': 'The blockchain is NOT valid! Tampering detected.'}
    return jsonify(response), 200

@app.route('/get_pending_transactions', methods=['GET'])
def get_pending_transactions_endpoint():
    """
    Returns the list of transactions currently waiting to be mined into a block.
    """
    response = {
        'pending_transactions': precursor_chain.pending_transactions,
        'count': len(precursor_chain.pending_transactions)
    }
    return jsonify(response), 200

if __name__ == '__main__':
    # Flask runs on port 5000 by default
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True allows for auto-reloading on code changes