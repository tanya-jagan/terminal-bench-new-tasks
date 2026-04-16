import socket
for ip in ['127.1.1.1','127.2.3.4','127.255.255.254']:
    s = socket.socket()
    try:
        s.bind((ip, 0))
        print('bind', ip)
    except Exception as e:
        print('fail', ip, e)
    finally:
        s.close()
