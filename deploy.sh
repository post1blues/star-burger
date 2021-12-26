#!/bin/bash

export BASE_DIR=/opt/star-burger/

echo "setup environment and git pull"
cd $BASE_DIR
source venv/bin/activate
git pull

echo "install requirements for python and js"
pip install -r requirements.txt
npm install --production

echo "build static and js"
python manage.py collectstatic
parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

echo "make migrations"
python manage.py migrate

echo "prepare systemd services"
systemctl restart star-burger.service
systemctl reload nginx.service

echo "Deploy is finished"
