FROM node:13 AS frontend

COPY . /app
WORKDIR /app

RUN npm install 
RUN npm run prod

# actual build
FROM python:3-slim-stretch


FROM python:3-slim-stretch

RUN apt-get update && apt-get install -y \
netbase \
build-essential

COPY . /data/
# copy generated assets
COPY --from=frontend /app/assets/ /data/assets
# copy generated index page
COPY --from=frontend /app/templates/ /data/templates
# install dependencies
RUN pip install -r /data/requirements.txt

COPY faucet.py /data/

ENTRYPOINT [ "python", "/data/faucet.py"]
CMD [ "start"]
