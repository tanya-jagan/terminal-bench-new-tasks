import socket

HOST = "127.0.0.1"
PORT = 9876

def query(password: str) -> str:
    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(password.encode() + b"\n")
    resp = s.recv(1024).decode().strip()
    s.close()
    return resp


if __name__ == "__main__":
    while True:
        p = input("guess> ").strip()
        print(query(p))