#!/usr/bin/env python3

import os
import sys
import logging
import argparse

# flask
from flask import Flask, jsonify, render_template, send_from_directory

# aeternity
from aeternity import node, signing
from aeternity.utils import is_valid_hash
from aeternity.openapi import OpenAPIClientException

# telegram
import telegram


# also log to stdout because docker
root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
root.addHandler(ch)

app = Flask(__name__, static_url_path='')

logging.getLogger("aeternity.epoch").setLevel(logging.WARNING)
# logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
# logging.getLogger("engineio").setLevel(logging.ERROR)

AE_UNIT = 1000000000000000000


def amount_to_ae(val):
    return f"{val/AE_UNIT:.0f}AE"


@app.after_request
def after_request(response):
    """enable CORS"""
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/')
def hello(name=None):
    amount = int(os.environ.get('TOPUP_AMOUNT', 5000000000000000000))
    network_id = os.environ.get('NETWORK_ID', "ae_uat")
    node_url = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "node@")
    node_url = f"{node_url} / {network_id}"
    explorer_url = os.environ.get("EXPLORER_URL", "https://testnet.explorer.aepps.com")
    return render_template('index.html', amount=f"{amount/1000000000000000000:.0f}", node=node_url, explorer_url=explorer_url)


@app.route('/assets/scripts/<path:filename>')
def serve_js(filename):
    return send_from_directory('assets/scripts', filename)


@app.route('/assets/styles/<path:filename>')
def serve_css(filename):
    return send_from_directory('assets/styles', filename)


@app.route('/assets/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('assets/images', filename)


@app.route('/account/<recipient_address>',  methods=['POST'])
def rest_faucet(recipient_address):
    """top up an account"""
    amount = int(os.environ.get('TOPUP_AMOUNT', 5000000000000000000))
    try:
        # validate the address
        logging.info(f"Top up request for {recipient_address}")
        if not is_valid_hash(recipient_address, prefix='ak'):
            return jsonify({"message": "The provided account is not valid"}), 400
        # sender account
        sender = signing.Account.from_private_key_string(os.environ.get('FAUCET_ACCOUNT_PRIV_KEY'))
        # payload
        payload = os.environ.get('TX_PAYLOAD', "Faucet Tx")
        # execute the spend transaction
        client = app.config.get("node_client")
        tx = client.spend(sender, recipient_address, amount, payload=payload)
        # print the full transaction
        balance = client.get_account_by_pubkey(pubkey=recipient_address).balance
        logging.info(f"Top up accont {recipient_address} of {amount} tx_hash: {tx.hash} completed")
        logging.debug(f"tx: {tx.tx}")
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Account `{recipient_address}` credited with {amount_to_ae(amount)} tokens on `{node}`. (tx hash: `{tx}`)"
        # return
        return jsonify({"tx_hash": tx.hash, "balance": balance})
    except OpenAPIClientException as e:
        logging.error(f"Api error: top up accont {recipient_address} of {amount} failed with error", e)
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Api error: top up accont {recipient_address} of {amount} on {node} failed with error {e}"
        return jsonify({"message": "The node is temporarily unavailable, please try again later"}), 503
    except Exception as e:
        logging.error(f"Generic error: top up accont {recipient_address} of {amount} failed with error", e)
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Api error: top up accont {recipient_address} of {amount} on {node} failed with error {e}"
        return jsonify({"message": "Unknow error, please contact aepp-dev[at]aeternity.com"}), 500
    finally:
        try:
            # telegram bot notifications
            enable_telegaram = os.environ.get('TELEGRAM_API_TOKEN', False)
            if enable_telegaram:
                token = os.environ.get('TELEGRAM_API_TOKEN', None)
                chat_id = os.environ.get('TELEGRAM_CHAT_ID', None)

                if token is None or chat_id is None:
                    logging.warning(f"missing chat_id ({chat_id}) or token {token} for telegram integration")
                bot = telegram.Bot(token=token)
                bot.send_message(chat_id=chat_id,
                                 text=notification_message,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            logging.error(f"Error delivering notifications", e)


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

    app.config['node_client'] = node.NodeClient(config=node.Config(
        external_url=os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com"),
        internal_url=os.environ.get('EPOCH_URL_DEBUG', "https://sdk-testnet.aepps.com"),
        network_id=os.environ.get('NETWORK_ID', "ae_uat"),
        force_compatibility=True,
    ))
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
