#!/usr/bin/env python3

import os
import argparse

# flask
from flask import Flask, jsonify, render_template, send_from_directory
from waitress import serve

# aeternity
from aeternity import node, signing
from aeternity.utils import is_valid_hash, format_amount
from aeternity.openapi import OpenAPIClientException

# telegram
import telegram

# caching
from expiringdict import ExpiringDict
from datetime import datetime, timedelta


app = Flask(__name__, static_url_path='')

# also log to stdout because docker
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ch.setFormatter(formatter)
# app.logger.addHandler(ch)

AE_UNIT = 1000000000000000000


def amount_to_ae(val):
    return f"{val/AE_UNIT:.0f}AE"


def pretty_time_delta(start, end):
    seconds = (start-end).total_seconds()
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd%dh%dm%ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh%dm%ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm%ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds)


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
    node_url = node_url
    explorer_url = os.environ.get("EXPLORER_URL", "https://testnet.explorer.aepps.com")
    return render_template('index.html', amount=f"{format_amount(amount)}", node=node_url, explorer_url=explorer_url)


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
    notification_message = ""
    try:
        # validate the address
        app.logger.info(f"Top up request for {recipient_address}")
        if not is_valid_hash(recipient_address, prefix='ak'):
            notification_message = "The provided account is not valid"
            return jsonify({"message": notification_message}), 400
        # check if the account is still in the cache
        registration_date = app.config['address_cache'].get(recipient_address)
        if registration_date is not None:
            graylist_exp = registration_date + timedelta(seconds=app.config['cache_max_age'])
            notification_message = f"The account `{recipient_address}` is graylisted for another {pretty_time_delta(graylist_exp, datetime.now())}"
            msg = f"The account is graylisted for another {pretty_time_delta(graylist_exp, datetime.now())}"
            return jsonify({"message": msg}), 425
        app.config['address_cache'][recipient_address] = datetime.now()
        # sender account
        sender = signing.Account.from_private_key_string(os.environ.get('FAUCET_ACCOUNT_PRIV_KEY'))
        # payload
        payload = os.environ.get('TX_PAYLOAD', "Faucet Tx")
        # execute the spend transaction
        client = app.config.get("node_client")
        tx = client.spend(sender, recipient_address, amount, payload=payload)
        # print the full transaction
        balance = client.get_account_by_pubkey(pubkey=recipient_address).balance
        app.logger.info(f"Top up accont {recipient_address} of {amount} tx_hash: {tx.hash} completed")
        app.logger.debug(f"tx: {tx.tx}")
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Account `{recipient_address}` credited with {format_amount(amount)} tokens on `{node}`. (tx hash: `{tx}`)"
        # return
        return jsonify({"tx_hash": tx.hash, "balance": balance})
    except OpenAPIClientException as e:
        app.logger.error(f"Api error: top up accont {recipient_address} of {amount} failed with error", e)
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Api error: top up accont {recipient_address} of {amount} on {node} failed with error {e}"
        return jsonify({"message": "The node is temporarily unavailable, please try again later"}), 503
    except Exception as e:
        app.logger.error(f"Generic error: top up accont {recipient_address} of {amount} failed with error", e)
        # notifications
        node = os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com").replace("https://", "")
        notification_message = f"Api error: top up accont {recipient_address} of {amount} on {node} failed with error {e}"
        return jsonify({"message": "Unknow error, please contact <a href=\"mailto:aepp-dev@aeternity.com\" class=\"hover:text-pink-lighter\">aepp-dev@aeternity.com</a>"}), 500
    finally:
        try:
            # telegram bot notifications
            enable_telegaram = os.environ.get('TELEGRAM_API_TOKEN', False)
            if enable_telegaram:
                token = os.environ.get('TELEGRAM_API_TOKEN', None)
                chat_id = os.environ.get('TELEGRAM_CHAT_ID', None)

                if token is None or chat_id is None:
                    app.logger.warning(f"missing chat_id ({chat_id}) or token {token} for telegram integration")
                bot = telegram.Bot(token=token)
                bot.send_message(chat_id=chat_id,
                                 text=notification_message,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            app.logger.error(f"Error delivering notifications", e)


#     ______  ____    ____  ______     ______
#   .' ___  ||_   \  /   _||_   _ `. .' ____ \
#  / .'   \_|  |   \/   |    | | `. \| (___ \_|
#  | |         | |\  /| |    | |  | | _.____`.
#  \ `.___.'\ _| |_\/_| |_  _| |_.' /| \____) |
#   `.____ .'|_____||_____||______.'  \______.'
#


def cmd_start(args=None):

    app.logger.info("faucet service started")

    app.config['node_client'] = node.NodeClient(config=node.Config(
        external_url=os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com"),
        internal_url=os.environ.get('EPOCH_URL_DEBUG', "https://sdk-testnet.aepps.com"),
        network_id=os.environ.get('NETWORK_ID', "ae_uat"),
        blocking_mode=True,
        force_compatibility=True,
    ))
    # instantiate the cache
    max_len = int(os.environ.get('CACHE_MAX_SIZE', 6000))
    max_age = int(os.environ.get('CACHE_MAX_AGE', 3600 * 4))  # default 4h
    app.config['cache_max_age'] = max_age
    app.config['address_cache'] = ExpiringDict(max_len=max_len, max_age_seconds=max_age)

    serve(app, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    commands = [
        {
            'name': 'start',
            'help': 'start the top up service',
            'target': cmd_start,
            'opts': []
        }
    ]
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'
    # register all the commands
    for c in commands:
        subparser = subparsers.add_parser(c['name'], help=c['help'])
        subparser.set_defaults(func=c['target'])
        # add the sub arguments
        for sa in c.get('opts', []):
            subparser.add_argument(*sa['names'],
                                   help=sa['help'],
                                   action=sa.get('action'),
                                   default=sa.get('default'))

    # parse the arguments
    args = parser.parse_args()
    # call the function
    args.func(args)
