"""
Implementation of an SMC client.

MODIFY THIS FILE.
"""
# You might want to import more classes if needed.

import collections
import json
import time
from typing import (
    Dict,
    Set,
    Tuple,
    Union
)

from communication import Communication
from expression import (
    Expression,
    Secret,
    Addition,
    Subtraction,
    Multiplication,
    Scalar
)
from protocol import ProtocolSpec
from secret_sharing import (
    reconstruct_secret,
    share_secret,
    Share,
)


# Feel free to add as many imports as you want.


class SMCParty:
    """
    A client that executes an SMC protocol to collectively compute a value of an expression together
    with other clients.

    Attributes:
        client_id: Identifier of this client
        server_host: hostname of the server
        server_port: port of the server
        protocol_spec (ProtocolSpec): Protocol specification
        value_dict (dict): Dictionary assigning values to secrets belonging to this client.
    """

    def __init__(
            self,
            client_id: str,
            server_host: str,
            server_port: int,
            protocol_spec: ProtocolSpec,
            value_dict: Dict[Secret, int]
    ):
        self.comm = Communication(server_host, server_port, client_id)

        self.client_id = client_id
        self.protocol_spec = protocol_spec
        self.value_dict = value_dict
        self.secrets = list(value_dict.keys())    #list of all secrets

        self.own_shares = dict()

    def run(self) -> int:
        """
        The method the client use to do the SMC.
        """
        # Create and share secrets across participants
        for s in self.secrets:
            shares = share_secret(self.value_dict[s], len(self.protocol_spec.participant_ids))

            for i, p_id in enumerate(self.protocol_spec.participant_ids):
                if p_id != self.client_id:
                    # Publish shares for other participants
                    self.comm.send_private_message(p_id, str(s.get_id_int()), str(shares[i].s_value))
                else:
                    # Keep own share in dict
                    self.own_shares[str(s.get_id_int())] = shares[i]

        # calculate final share
        final_share = self.process_expression(self.protocol_spec.expr).s_value

        # send final share to others
        self.comm.publish_message("final", str(final_share))

        # put every share of the circuit together
        final_res = Share(final_share)

        for p_id in self.protocol_spec.participant_ids:

            if p_id != self.client_id:
                remote_share = self.comm.retrieve_public_message(p_id, "final")

                while remote_share is None:  # retry if not yet here

                    remote_share = self.comm.retrieve_public_message(p_id, "final")
                final_res += Share(int(remote_share))

        return final_res.s_value
        


    def process_expression(self, expr: Expression, secret_in_mult = False):

        # if expr is an addition operation:
        if isinstance(expr, Addition):
            return(self.process_addition(expr))

        # if expr is a subtraction operation:
        if isinstance(expr, Subtraction):
            return(self.process_subtraction(expr))

        # if expr is a multiplication operation:
        if isinstance(expr, Multiplication):
            return(self.process_multiplication(expr,secret_in_mult))

        # if expr is a secret:
        if isinstance(expr, Secret):
            return(self.process_secret(expr))

        # if expr is a scalar:
        if isinstance(expr, Scalar):
            return(self.process_scalar(expr,secret_in_mult))


    def search_share(self, expr_id) -> int:
        """Search for corresponding secret on the server"""
        return int(self.comm.retrieve_private_message(str(expr_id)))



    def contains_secret(self, expr):
        if isinstance(expr, Secret):
            return True
        elif isinstance(expr, Scalar):
            return False
        else:
            return self.contains_secret(expr.e1) or self.contains_secret(expr.e2)

    # Feel free to add as many methods as you want.

    def process_addition(self,expr):
        return self.process_expression(expr.e1) + self.process_expression(expr.e2)

    def process_subtraction(self,expr):
        return self.process_expression(expr.e1) - self.process_expression(expr.e2)

    def process_multiplication(self,expr,secret_in_mult):
        if self.contains_secret(expr.e1) and self.contains_secret(expr.e2):  # secret*secret

            x = self.process_expression(expr.e1, True)
            y = self.process_expression(expr.e2, True)

            x_minus_a, y_minus_b, c = self.get_broadcast_val(x, y, expr)

            if self.client_id == self.protocol_spec.participant_ids[0]:  # participant 0 add the constant
                return Share(c + x.s_value * y_minus_b + y.s_value * x_minus_a - x_minus_a * y_minus_b)
            else:
                return Share(c + x.s_value * y_minus_b + y.s_value * x_minus_a)
        else:
            secret_mult = self.contains_secret(expr.e1) or self.contains_secret(expr.e2) or secret_in_mult

            return self.process_expression(expr.e1, secret_mult) * self.process_expression(expr.e2, secret_mult)

    def process_scalar(self,expr,secret_in_mult):
        # scalar should only be added by one participant in case of addition
        if (self.protocol_spec.participant_ids[0] != self.client_id) and (not secret_in_mult):
            return Share(0)
        else:
            return Share(expr.value)

    def process_secret(self,expr):
        if str(expr.get_id_int()) in self.own_shares.keys():
            return self.own_shares[str(expr.get_id_int())]
        else:
            return Share(self.search_share(expr.get_id_int()))

    def get_broadcast_val(self, s: Share, v: Share, expr):

        op_id_str = str(expr.get_id_int())

        a, b, c = self.comm.retrieve_beaver_triplet_shares(op_id_str)
        s = s.s_value
        v = v.s_value
        a = a.s_value
        b = b.s_value

        # send to others shares of x-a and y-b
        s_minus_a = s - a  # d
        v_minus_b = v - b  # e

        # everyone can see these values and get the original value
        self.comm.publish_message(self.client_id + "s_minus_a_" + op_id_str, str(s_minus_a))
        self.comm.publish_message(self.client_id + "v_minus_b_" + op_id_str, str(v_minus_b))

        # reconstruct x-a and y-b

        d_shares = s_minus_a
        e_shares = v_minus_b

        for p_id in self.protocol_spec.participant_ids:

            if p_id != self.client_id:

                curr_d = self.comm.retrieve_public_message(p_id, p_id + "s_minus_a_" + op_id_str)
                curr_e = self.comm.retrieve_public_message(p_id, p_id + "v_minus_b_" + op_id_str)

                while curr_d is None:
                    # wait for others to upload their shares. Avoid deadlock
                    curr_x = self.comm.retrieve_public_message(p_id, p_id + "s_minus_a_" + op_id_str)

                while curr_e is None:
                    curr_y = self.comm.retrieve_public_message(p_id, p_id + "v_minus_b_" + op_id_str)

                d_shares += int(curr_d)
                e_shares += int(curr_e)

        return d_shares, e_shares, c.s_value