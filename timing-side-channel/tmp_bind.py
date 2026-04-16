import socket
for ip in ['127.0.0.1','127.0.0.2','127.0.0.3']:
    s = socket.socket()
    try:
        s.bind((ip, 0))
        print('bind', ip)
    except Exception as e:
        print('fail', ip, e)
    finally:
        s.close()
