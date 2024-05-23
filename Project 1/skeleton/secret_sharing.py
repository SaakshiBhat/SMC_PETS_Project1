"""
Secret sharing scheme.
MODIFY THIS FILE.
"""

from __future__ import annotations
import random
import pickle
import json

from typing import List,Set


class Share:
    """
    A secret share in a finite field.
    """

    def __init__(self, s_value: int = 0):                  #s_value is the share value
        self.s_value = s_value
        #raise NotImplementedError("You need to implement this method.")

    def __repr__(self):
        return f"Share : {self.s_value}"
        #raise NotImplementedError("You need to implement this method.")

    def __add__(self, other):
        val = (self.s_value + other.s_value) % get_mod()
        return Share(val)
        #raise NotImplementedError("You need to implement this method.")

    def __sub__(self, other):
        val = (self.s_value - other.s_value) % get_mod()
        return Share(val)
        #raise NotImplementedError("You need to implement this method.")

    def __mul__(self, other):
        val = (self.s_value * other.s_value) % get_mod()
        return Share(val)
        #raise NotImplementedError("You need to implement this method.")

    def serialize(self):
        """Generate a representation suitable for passing in a message."""
        share_dict = {'value': self.s_value}
        # Serialize the dictionary to a JSON string
        return json.dumps(share_dict)


    @staticmethod
    def deserialize(serialized) -> Share:
        """Restore object from its serialized representation."""
        # Deserialize the JSON string to a dictionary
        share_dict = json.loads(serialized)
        # Convert the dictionary back to a Share object
        return Share(share_dict['value'])


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """Generate secret shares."""
    last_share = secret
    shares_list = []

    #Assign random values to first n-1 people and (secret-sum) to the last one
    for i in range(num_shares - 1):
        share_value = random.randint(0,get_mod())
        shares_list.append(Share(share_value))
        last_share = last_share - share_value       #Subtract in each step

    shares_list.append(Share(last_share))
    return shares_list
    #raise NotImplementedError("You need to implement this method.")


def reconstruct_secret(shares: List[Share]) -> int:
    """Reconstruct the secret from shares."""
    res = 0
    for i in shares:
        res += i.s_value
    return res
    #raise NotImplementedError("You need to implement this method.")


limit = 2**64
def get_mod() -> int:
    return limit
