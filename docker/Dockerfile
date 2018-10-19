FROM rust as builder

ADD . /tmp/src
RUN cd /tmp/src && rm -rf target && cargo test && cargo build --release


FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y libpq-dev wget

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY --from=builder /tmp/src/target/release/mailboxer /mailboxer

EXPOSE 8000
EXPOSE 2525

CMD dockerize -timeout 3600s -wait tcp://db:5432 /mailboxer
