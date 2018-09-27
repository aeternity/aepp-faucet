# aepp-faucet
Send Online Top-up. Instant Wallet Recharge


Recharge your wallet on the aeternity testnet https://sdk-testnet.aepps.com

## Configuration
Configuring Faucet application via enviornment variable: 

- `TOPUP_AMOUNT` The amount of tokens that the faucet application will place into your account. (Default value 250)
- `FAUCET_ACCOUNT_PRIV_KEY` The account that faucet aepp will top off the account.
- `EPOCH_URL` URL of the node that the faucet aepp is using. (Default value 'https://sdk-testnet.aepps.com')
- `TX_TTL`  How many key blocks will live before it is mined  (Default value 100)

## Example Usage
```
curl -X POST http://faucet.aepps.com/account/ak_kcCLR4GVfBpX6ctFMeXJh33eQT7Cky5SfVzDczDMNo5QM4vyt
```
