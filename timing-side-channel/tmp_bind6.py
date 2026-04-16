import socket
for ip in ['::1','::2','::3','::4']:
    s = socket.socket(socket.AF_INET6)
    try:
        s.bind((ip, 0))
        print('bind6', ip)
    except Exception as e:
        print('fail6', ip, e)
    finally:
        s.close()
