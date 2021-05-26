# front-end build
FROM node:15 AS frontend

COPY ./frontend /app
WORKDIR /app

RUN npm install && npm run prod

# actual build
FROM node:15

# use app directory
WORKDIR /app

# copy generated assets
COPY --from=frontend /app/assets ./assets
# copy generated index page
COPY --from=frontend /app/templates ./templates
# copy package.json & package-lock.json
COPY package*.json .
# copy node files
COPY faucet.js .
# building your code for production
RUN npm ci --only=production

# Bundle app source
COPY . .

# run the app
CMD [ "node", "faucet.js"]
