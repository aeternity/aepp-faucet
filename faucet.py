#!/usr/bin/env python3

import os
import argparse

# flask
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import cross_origin
from waitress import serve

# aeternity
from aeternity import node, signing
from aeternity.utils import is_valid_hash, format_amount, amount_to_aettos
from aeternity.openapi import OpenAPIClientException

# telegram
import telegram

# caching
from expiringdict import ExpiringDict
from datetime import datetime, timedelta

# logging
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__, static_url_path='')

# environment var
FAUCET_ACCOUNT_PRIV_KEY = os.environ.get("FAUCET_ACCOUNT_PRIV_KEY")
TOPUP_AMOUNT = amount_to_aettos(os.environ.get("TOPUP_AMOUNT", "5AE"))
SPEND_TX_PAYLOAD = os.environ.get("SPEND_TX_PAYLOAD", "Faucet Tx")
NODE_URL = os.environ.get("NODE_URL", "https://testnet.aeternity.io")
EXPLORER_URL = os.environ.get("EXPLORER_URL", "https://testnet.aeternal.io")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "aepp-dev@aeternity.com")
# telegram notifications
TELEGRAM_API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN', False)
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
# graylisting
CACHE_MAX_SIZE = int(os.environ.get('CACHE_MAX_SIZE', 6000))
CACHE_MAX_AGE = int(os.environ.get('CACHE_MAX_AGE', 3600 * 4))  # default 4h
# Server
SERVER_LISTEN_ADDRESS = os.environ.get("SERVER_LISTEN_ADDRESS", "0.0.0.0")
SERVER_LISTEN_PORT = int(os.environ.get("SERVER_LISTEN_PORT", 5000))


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
    return render_template('index.html', amount=f"{format_amount(TOPUP_AMOUNT)}", node=NODE_URL, explorer_url=EXPLORER_URL)


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
@cross_origin()
def rest_faucet(recipient_address):
    """top up an account"""
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
        sender = signing.Account.from_private_key_string(FAUCET_ACCOUNT_PRIV_KEY)
        # execute the spend transaction
        client = app.config.get("node_client")
        tx = client.spend(sender, recipient_address, TOPUP_AMOUNT, payload=SPEND_TX_PAYLOAD)
        # print the full transaction
        balance = client.get_account_by_pubkey(pubkey=recipient_address).balance
        app.logger.info(f"Top up account {recipient_address} of {TOPUP_AMOUNT} tx_hash: {tx.hash} completed")
        app.logger.debug(f"tx: {tx.tx}")
        # notifications
        node = NODE_URL.replace("https://", "")
        notification_message = f"Account `{recipient_address}` credited with {format_amount(TOPUP_AMOUNT)} tokens on `{node}`. (tx hash: `{tx}`)"
        # return
        return jsonify({"tx_hash": tx.hash, "balance": balance})
    except OpenAPIClientException as e:
        app.logger.error(f"API error: top up account {recipient_address} of {TOPUP_AMOUNT} failed with error", e)
        # notifications
        node = NODE_URL.replace("https://", "")
        notification_message = f"API error: top up account {recipient_address} of {TOPUP_AMOUNT} on {node} failed with error {e}"
        return jsonify({"message": "The node is temporarily unavailable, please try again later"}), 503
    except Exception as e:
        app.logger.error(f"Generic error: top up account {recipient_address} of {TOPUP_AMOUNT} failed with error", e)
        # notifications
        node = NODE_URL.replace("https://", "")
        notification_message = f"API error: top up account {recipient_address} of {TOPUP_AMOUNT} on {node} failed with error {e}"
        return jsonify({"message": f"""Unknown error, please contact
        <a href="{SUPPORT_EMAIL}" class="hover:text-pink-lighter">{SUPPORT_EMAIL}</a>"""}), 500
    finally:
        try:
            # telegram bot notifications
            if TELEGRAM_API_TOKEN:
                if TELEGRAM_CHAT_ID is None or TELEGRAM_API_TOKEN is None:
                    app.logger.warning(f"missing chat_id ({TELEGRAM_CHAT_ID}) or token {TELEGRAM_API_TOKEN} for telegram integration")
                bot = telegram.Bot(token=TELEGRAM_API_TOKEN)
                bot.send_message(chat_id=TELEGRAM_CHAT_ID,
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
        external_url=NODE_URL,
        blocking_mode=True,
        force_compatibility=True,
    ))
    # instantiate the cache
    app.config['cache_max_age'] = CACHE_MAX_AGE
    app.config['address_cache'] = ExpiringDict(
        max_len=CACHE_MAX_SIZE,
        max_age_seconds=CACHE_MAX_AGE)

    serve(app, host=SERVER_LISTEN_ADDRESS, port=SERVER_LISTEN_PORT)


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
