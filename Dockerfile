FROM python:3.7-slim-stretch

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential python-dev wget

WORKDIR /app

COPY . .

RUN wget https://raw.githubusercontent.com/eficode/wait-for/master/wait-for
RUN chmod +x wait-for
RUN mv wait-for /usr/bin

RUN pip install --editable .[dev]

RUN rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove gcc build-essential python-dev
VOLUME ["/root/.aws"]
