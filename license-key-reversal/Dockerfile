FROM ubuntu:24.04

RUN apt-get -o Acquire::ForceIPv4=true update && \
    apt-get install -y \
    gcc \
    python3 \
    binutils \
    file \
    xxd && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY licensechecker /app/licensechecker
COPY test_solution.py /app/test_solution.py

RUN chmod +x /app/licensechecker

CMD ["/bin/bash"]