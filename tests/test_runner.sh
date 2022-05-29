#!/bin/bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -a -q) --force
docker volume rm $(docker volume ls -q --filter dangling=true)
docker network prune --force
docker-compose up -d --no-recreate
docker-compose logs -f tests
