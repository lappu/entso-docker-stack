# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Install git
RUN apt-get update && \
    apt-get install -y git default-libmysqlclient-dev python3-dev build-essential curl

# Set the working directory to /app
WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY pyproject.toml poetry.lock /app

RUN /root/.local/bin/poetry install

# Copy the current directory contents into the container at /app
COPY . /app

CMD ["/root/.local/bin/poetry", "run", "python", "run.py"]
