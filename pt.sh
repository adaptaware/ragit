#!/usr/bin/bash

python3 -m pytest -c /vagrant/.pytest.ini \
    --cov-config=/vagrant/.coveragerc \
    --cov=. \
    --cov-report term-missing


