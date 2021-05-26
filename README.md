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

### Logging
- `FAUCET_LOG_LEVEL` the winston log-level to use (Default: `info`)

### Server
- `SERVER_LISTEN_ADDRESS` which address to listen to (Default: `0.0.0.0`)
- `SERVER_LISTEN_PORT` on which port to listen (Default: `5000`)

## Development

This repository bundles a simple frontend and a node (express) based backend into a single docker container.

To build and run it locally execute following commands in the root:
```
make docker-build
make docker-run
```

### Notes:
- The `frontend/index.html` is transformed into `index.mustache` in order to allow the node backend to provide dynamic values using the [Mustache](https://mustache.github.io/) template engine.