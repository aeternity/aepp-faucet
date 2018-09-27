#!/usr/bin/env python3

import os
import sys
import logging
import argparse

# flask
from flask import Flask, jsonify, render_template

# aeternity
from aeternity.epoch import EpochClient
from aeternity.signing import Account
from aeternity.utils import is_valid_hash
from aeternity.openapi import OpenAPIClientException
from aeternity.config import Config


# also log to stdout because docker
root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
root.addHandler(ch)

app = Flask(__name__)

logging.getLogger("aeternity.epoch").setLevel(logging.WARNING)
# logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
# logging.getLogger("engineio").setLevel(logging.ERROR)


@app.after_request
def after_request(response):
    """enable CORS"""
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/')
def hello(name=None):
    amount = int(os.environ.get('TOPUP_AMOUNT', 250))
    return render_template('index.html', amount=amount)


@app.route('/account/<recipient_address>',  methods=['POST'])
def rest_faucet(recipient_address):
    """top up an account"""
    # recipient_address = request.form.get("account")
    # validate the address
    logging.info(f"Top up request for {recipient_address}")
    if len(recipient_address.strip()) < 3 or not is_valid_hash(recipient_address, prefix='ak'):
        return jsonify({"message": "bad request"}), 400

    # genesys key
    bank_wallet_key = os.environ.get('FAUCET_ACCOUNT_PRIV_KEY')
    kp = Account.from_private_key_string(bank_wallet_key)
    # target node
    Config.set_defaults(Config(
        external_url=os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com"),
        internal_url=os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com"),
    ))
    # amount
    amount = int(os.environ.get('TOPUP_AMOUNT', 250))
    ttl = int(os.environ.get('TX_TTL', 100))
    client = EpochClient()
    tx = client.spend(kp, recipient_address, amount, tx_ttl=ttl)
    balance = client.get_account_by_pubkey(pubkey=recipient_address).balance
    logging.info(f"top up accont {recipient_address} of {amount} tx_ttl:{ttl} tx_hash: {tx}")
    return jsonify({"tx_hash": tx, "balance": balance})

#     ______  ____    ____  ______     ______
#   .' ___  ||_   \  /   _||_   _ `. .' ____ \
#  / .'   \_|  |   \/   |    | | `. \| (___ \_|
#  | |         | |\  /| |    | |  | | _.____`.
#  \ `.___.'\ _| |_\/_| |_  _| |_.' /| \____) |
#   `.____ .'|_____||_____||______.'  \______.'
#


def cmd_start(args=None):
    root.addHandler(app.logger)
    logging.info("faucet service started")
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    cmds = [
        {
            'name': 'start',
            'help': 'start the top up service',
            'opts': []
        }
    ]
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'
    # register all the commands
    for c in cmds:
        subp = subparsers.add_parser(c['name'], help=c['help'])
        # add the sub arguments
        for sa in c.get('opts', []):
            subp.add_argument(*sa['names'],
                              help=sa['help'],
                              action=sa.get('action'),
                              default=sa.get('default'))

    # parse the arguments
    args = parser.parse_args()
    # call the command with our args
    ret = getattr(sys.modules[__name__], 'cmd_{0}'.format(
        args.command.replace('-', '_')))(args)
