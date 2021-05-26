# Aepp-faucet

Send Online Top-up. Instant Account Recharge

Recharge your account on the Aeternity Testnet

## Configuration

Configuring Faucet application via environment variable:

- `FAUCET_ACCOUNT_PRIV_KEY` The account that faucet aepp will top off the account. (Required)
- `TOPUP_AMOUNT` The amount of tokens that the faucet application will place into your account. (Default: 5AE)
- `SPEND_TX_PAYLOAD` Value to use to fill the payload for the transactions (Default: `Faucet Tx`)
- `NODE_URL` URL of the node that the faucet aepp is using. (Default: 'https://testnet.aeternity.io')
- `EXPLORER_URL` URL of the explorer app (Default: 'https://testnet.aeternal.io')
- `SUPPORT_EMAIL` Email to display for support requests (Default: `aepp-dev@aeternity.com`)

### Telegram integration

- `TELEGRAM_API_TOKEN` the token of the telegram bot, if not set telegram integration will be disabled
- `TELEGRAM_CHAT_ID` the chat id to send notifications to

### Server
- `SERVER_LISTEN_ADDRESS` which address to listen to (Default: `0.0.0.0`)
- `SERVER_LISTEN_PORT` on which port to listen (Default: `5000`)

## Development

### Back-End

1. Run `pip install -r requirements.txt` to install the python dependencies

### Frontend 

1. Switch to the `frontend` folder of the project
1. Run `npm i` from
1. Run `npm run dev` to start webpack

**Notes**:
- All the frontend resources are in `frontend/`
- Run `npm run prod` in this folder to compile assets for production
- Compiled assets (`prod` or `dev`) will be created in `frontend/assets/`
- Index file from `frontend/src` will be created in `frontend/templates/index.html`


