#!/bin/bash

docker-compose down
docker-compose pull
docker-compose up -d --build
docker-compose logs -f tests
