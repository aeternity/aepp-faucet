FROM node:lts-alpine as nodebuilder

# Add required files to download and compile only the dependencies
COPY src /build/src
COPY templates /build/templates
COPY package-lock.json package.json *.config.js /build/

RUN cd /build && npm install && npm run prod


FROM python:3-slim-stretch

RUN apt-get update && apt-get install -y \
netbase \
build-essential

COPY --from=nodebuilder /build/assets /data/assets
COPY --from=nodebuilder /build/templates /data/templates

COPY requirements.txt /data/
RUN pip install -r /data/requirements.txt

COPY faucet.py /data/

ENTRYPOINT [ "python", "/data/faucet.py"]
CMD [ "start"]
