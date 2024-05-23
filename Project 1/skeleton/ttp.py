"""
Trusted parameters generator.

MODIFY THIS FILE.
"""

import collections
import random
from typing import (
    Dict,
    Set,
    Tuple,
)

from communication import Communication
from secret_sharing import(
    share_secret,
    Share,
    get_mod
)

# Feel free to add as many imports as you want.


class TrustedParamGenerator:
    """
    A trusted third party that generates random values for the Beaver triplet multiplication scheme.
    """

    def __init__(self):
        self.participant_ids: Set[str] = set()
        self.beaver_triplet_shares :  Dict[str,Dict[str, Tuple[Share, Share, Share]]] = dict()
        #Each participant gets different beaver triplet


    def add_participant(self, participant_id: str) -> None:
        """
        Add a participant.
        """
        self.participant_ids.add(participant_id)

    def retrieve_share(self, client_id: str, op_id: str) -> Tuple[Share, Share, Share]:
        """
        Retrieve a triplet of shares for a given client_id.
        """

        #If triplet is not already generated for that operation
        if op_id not in self.beaver_triplet_shares.keys():
            self.gen_beaver_triplets(op_id)

        return self.beaver_triplet_shares[op_id][client_id]


        #raise NotImplementedError("You need to implement this method.")

    def gen_beaver_triplets(self, op_id):
        """Generates a new dictionary containing all beaver triplets for each client for a specific operation
        indexed by op_id """

        # Triplets are different for different operation and client.

        a = random.randint(0, get_mod())
        b = random.randint(0, get_mod())

        c = a*b

        # create shares of beaver triplets
        a_shares = share_secret(a, len(self.participant_ids))
        b_shares = share_secret(b, len(self.participant_ids))
        c_shares = share_secret(c, len(self.participant_ids))


        #Dict for saving shares for each client
        temp_dict = dict()
        for i, name in enumerate(self.participant_ids):
            l = list()
            l.append(a_shares[i])
            l.append(b_shares[i])
            l.append(c_shares[i])

            temp_dict[name] = tuple(l)

        # index dict w.r.t the operation id
        self.beaver_triplet_shares[op_id] = temp_dict

    # Feel free to add as many methods as you want.
