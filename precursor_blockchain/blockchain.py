import hashlib
import json
from datetime import datetime

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions # A list of transactions
        self.previous_hash = previous_hash
        self.nonce = nonce # Nonce for Proof of Work
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        # We need a consistent way to stringify the transactions list
        # json.dumps ensures consistent ordering of dictionary keys
        transactions_string = json.dumps(self.transactions, sort_keys=True)
        block_string = f"{self.index}{self.timestamp}{transactions_string}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        # Convert Block object to a dictionary for JSON serialization
        return {
            'index': self.index,
            'timestamp': str(self.timestamp), # Convert datetime to string
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }

    @staticmethod
    def from_dict(block_dict):
        # Recreate Block object from a dictionary
        return Block(
            block_dict['index'],
            datetime.fromisoformat(block_dict['timestamp']), # Convert string back to datetime
            block_dict['transactions'],
            block_dict['previous_hash'],
            block_dict['nonce']
            # hash will be recalculated by constructor
        )

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = 4 # Number of leading zeros required for PoW
        self.create_genesis_block()

    def create_genesis_block(self):
        # Genesis block does not have any transactions initially, and no previous hash
        self.chain.append(self.mine_block(Block(0, datetime.now(), [], "0", 0)))
        print("Genesis Block created.")

    def get_latest_block(self):
        return self.chain[-1]

    def new_transaction(self, sender_urn, recipient_urn, chemical_urn, quantity, unit, event_type, details):
        """
        Creates a new transaction to go into the next mined block.
        """
        transaction = {
            'sender_urn': sender_urn,
            'recipient_urn': recipient_urn,
            'chemical_urn': chemical_urn,
            'quantity': quantity,
            'unit': unit,
            'event_type': event_type, # e.g., 'RECEIVE', 'SHIPMENT', 'CONSUMPTION', 'ADJUSTMENT'
            'timestamp': datetime.now().isoformat(),
            'details': details # Any additional relevant details
        }
        self.pending_transactions.append(transaction)
        print(f"Transaction added to pending: {event_type} {chemical_urn}")
        # Return the index of the block that this transaction will be added to
        # (which is the index of the next block to be mined)
        return self.get_latest_block().index + 1

    def proof_of_work(self, previous_hash):
        """
        Simple Proof of Work algorithm:
         - Find a number 'nonce' such that hashing (previous_hash + nonce) results in a hash with 'self.difficulty' leading zeros.
        """
        nonce = 0
        while True:
            guess_hash = hashlib.sha256(f"{previous_hash}{nonce}".encode()).hexdigest()
            if guess_hash.startswith('0' * self.difficulty):
                return nonce
            nonce += 1

    def mine_block(self, new_block=None):
        """
        Mines a new block, appending pending transactions.
        If new_block is None, it creates a new block with pending transactions.
        If new_block is provided (e.g., for genesis), it uses that.
        """
        if new_block is None:
            previous_block = self.get_latest_block()
            nonce = self.proof_of_work(previous_block.hash) # Find nonce based on previous block's hash
            new_block = Block(
                previous_block.index + 1,
                datetime.now(),
                list(self.pending_transactions), # Copy pending transactions
                previous_block.hash,
                nonce
            )
            self.pending_transactions = [] # Clear pending transactions after they are included
            print(f"Block #{new_block.index} mined with nonce {nonce}.")
        
        # Calculate final hash with determined nonce
        new_block.hash = new_block.calculate_hash()
        return new_block


    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Re-calculate the hash of the current block to verify its integrity
            if current_block.hash != current_block.calculate_hash():
                print(f"ERROR: Block #{current_block.index} has been tampered with (hash mismatch)!")
                return False

            # Check if the current block points to the correct previous hash
            if current_block.previous_hash != previous_block.hash:
                print(f"ERROR: Block #{current_block.index} does not link correctly to previous block!")
                return False
            
            # Verify Proof of Work for the current block
            # This means checking if its hash starts with the required number of zeros
            if not current_block.hash.startswith('0' * self.difficulty):
                print(f"ERROR: Block #{current_block.index} failed Proof of Work verification!")
                return False

        return True

    def save_chain(self, filename="blockchain_data.json"):
        # Convert chain of Block objects to list of dictionaries for JSON serialization
        chain_data = [block.to_dict() for block in self.chain]
        with open(filename, 'w') as f:
            json.dump(chain_data, f, indent=4)
        print(f"Blockchain saved to {filename}")

    def load_chain(self, filename="blockchain_data.json"):
        try:
            with open(filename, 'r') as f:
                chain_data = json.load(f)
            self.chain = [Block.from_dict(block_dict) for block_dict in chain_data]
            print(f"Blockchain loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"No existing blockchain data found at {filename}. Starting new chain.")
            return False
        except Exception as e:
            print(f"Error loading blockchain: {e}. Starting new chain.")
            return False