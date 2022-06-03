FROM python:3.9.3-slim-buster
ARG PORT
WORKDIR /app
COPY . /app
RUN bash -c "./packages_installer.sh"
EXPOSE $PORT
ENTRYPOINT python main.py
