#!/bin/bash

export BASE_DIR=/opt/star-burger/

echo "setup environment and git pull"

cd $BASE_DIR
source venv/bin/activate
git pull

echo "install requirements for python and js"
pip install -r requirements.txt
npm install --production -

echo "build static and js"
parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python manage.py collectstatic

echo "make migrations"
python manage.py migrate

echo "prepare systemd services"
systemctl restart star-burger.service
systemctl reload nginx.service

curl --header "Content-Type: application/json" \
     --header "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" \
     --request POST \
     --data "{\"environment\": \"$ROLLBAR_ENV\", \"revision\": \"$(git rev-parse --short HEAD)\"}" \
     https://api.rollbar.com/api/1/deploy

echo "Deploy is finished"
