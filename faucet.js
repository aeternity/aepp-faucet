const path = require('path');
const express = require('express');
const mustache = require('mustache-express');
const winston = require('winston');
const NodeCache = require('node-cache');
const { DateTime } = require("luxon");
const { Universal, AmountFormatter, Crypto, MemoryAccount, Node } = require('@aeternity/aepp-sdk');

const app = express();

const setRequiredVariable = (variableName) => {
    if (process.env[variableName]) {
        return process.env[variableName];
    }
    throw new Error(`ENV-variable missing: ${variableName}`);
}

// faucet transactions
const FAUCET_ACCOUNT_PRIV_KEY = setRequiredVariable('FAUCET_ACCOUNT_PRIV_KEY');
const TOPUP_AMOUNT = process.env.TOPUP_AMOUNT || '5';
const SPEND_TX_PAYLOAD = process.env.SPEND_TX_PAYLOAD || 'Faucet Tx';
// node, explorer & support
const NODE_URL = process.env.NODE_URL || 'https://testnet.aeternity.io';
const EXPLORER_URL = process.env.EXPLORER_URL || 'https://explorer.testnet.aeternity.io';
const SUPPORT_EMAIL = process.env.SUPPORT_EMAIL || 'aepp-dev@aeternity.com';
// graylisting
const CACHE_MAX_SIZE = process.env.CACHE_MAX_SIZE || 6000;
const CACHE_MAX_AGE = process.env.CACHE_MAX_AGE || 3600 * 4; // default 4h
// logging
const FAUCET_LOG_LEVEL = process.env.FAUCET_LOG_LEVEL || 'info';
// server
const SERVER_LISTEN_ADDRESS = process.env.SERVER_LISTEN_ADDRESS || '0.0.0.0';
const SERVER_LISTEN_PORT = process.env.SERVER_LISTEN_PORT || 5000;

const KEYPAIR = {
    secretKey: FAUCET_ACCOUNT_PRIV_KEY,
    publicKey: Crypto.getAddressFromPriv(FAUCET_ACCOUNT_PRIV_KEY)
};

const logger = winston.createLogger({
    level: FAUCET_LOG_LEVEL,
    format: winston.format.combine(
        winston.format.errors({ stack: true }),
        winston.format.simple(),
        winston.format.timestamp(),
        winston.format.printf(info => `[${info.timestamp}] ${info.level.toUpperCase()} - ${info.message}`)
    ),
    transports: [new winston.transports.Console()]
});

const address_cache = new NodeCache({
    maxKeys: CACHE_MAX_SIZE,
    stdTTL: CACHE_MAX_AGE,
    checkperiod: 60
});

const initClient = async () => {
    const node = await Node({ url: NODE_URL });
    return Universal({
        nodes: [
            { name: 'node', instance: node },
        ],
        accounts: [MemoryAccount({ keypair: KEYPAIR })],
    });
};

const run = async () => {
    // initialize SDK
    const client = await initClient();

    // set up mustache templating
    app.engine('mustache', mustache());
    app.set('view engine', 'mustache');
    app.set('views', `${__dirname}/templates`);

    // static assets
    app.use('/assets', express.static(path.join(__dirname, 'assets')));

    // serve frontend
    app.get('/', (req, res) => {
        res.render('index', {amount: `${TOPUP_AMOUNT} AE`, node: NODE_URL, explorer_url: EXPLORER_URL});
    });

    // top up address
    app.post('/account/:recipient_address', async (req, res) => {
        const address = req.params.recipient_address;
        let message = '';
        try {
            logger.info(`Top up request for ${address}`);
            // validate address
            if(!Crypto.isAddressValid(address)) {
                message = `The provided address is not valid: ${address}`;
                logger.error(message);
                res.status(400);
                res.send({message});
                return;
            }
            // check if address is still in cache
            const top_up_date = address_cache.get(address);
            if(top_up_date) {
                const graylist_exp_date = top_up_date.plus({seconds: CACHE_MAX_AGE});
                const delta = graylist_exp_date.diffNow().toFormat("h'h' mm'm' ss's'");
                message = `The address ${address} is graylisted for another ${delta}`;;
                logger.warn(message);
                res.status(425);
                res.send({message});
                return;
            }
            address_cache.set(address, DateTime.now());
            const tx = await client.spend(AmountFormatter.toAettos(TOPUP_AMOUNT), address, { payload: SPEND_TX_PAYLOAD });
            logger.info(`Top up address ${address} with ${TOPUP_AMOUNT} AE tx_hash: ${tx.hash} completed.`);
            logger.debug(JSON.stringify(tx));
            message = `Address ${address} credited with ${TOPUP_AMOUNT} AE tokens on ${NODE_URL.replace('https://', '')}. (tx hash: ${tx.hash})`;
            const new_balance = await client.getBalance(address);
            res.send({tx_hash: tx.hash, balance: new_balance});
        } catch (err) {
            message = `Generic error: top up account ${address} of ${TOPUP_AMOUNT} AE on ${NODE_URL.replace('https://', '')} failed with error.`;
            logger.error(message, err);
            res.send({message: `""Unknown error, please contact <a href="${SUPPORT_EMAIL}" class="hover:text-pink-lighter">${SUPPORT_EMAIL}</a>""`});
        }
    });

    app.listen(SERVER_LISTEN_PORT, SERVER_LISTEN_ADDRESS, async () => {
        logger.info(`Faucet listening at http://${SERVER_LISTEN_ADDRESS}:${SERVER_LISTEN_PORT}`);
        logger.info(`Faucet Address: ${KEYPAIR.publicKey}`);
        const balance = await client.getBalance(KEYPAIR.publicKey);
        logger.info(`Faucet Balance: ${AmountFormatter.toAe(balance)} AE`);
        logger.info(`Log-level: ${FAUCET_LOG_LEVEL}`);
    });
}

run();