FROM ubuntu:24.04

RUN apt-get update && apt-get install -y python3 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# agent user 
RUN useradd -m agent

# service (agent cannot read) 
WORKDIR /opt
COPY opt/login.py /opt/login.py
COPY opt/start.sh /opt/start.sh
RUN chown root:root /opt/login.py /opt/start.sh \
    && chmod 700 /opt/login.py /opt/start.sh

# agent
WORKDIR /app
COPY app/client.py /app/client.py
COPY app/test_outputs.py /app/test_outputs.py
RUN chown -R agent:agent /app \
    && chmod 755 /app/client.py /app/test_outputs.py

CMD ["/opt/start.sh"]