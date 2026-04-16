import socket
for ip in ['192.168.0.200','10.0.0.200','172.16.0.50']:
    s = socket.socket()
    try:
        s.bind((ip, 0))
        print('bind', ip)
    except Exception as e:
        print('fail', ip, e)
    finally:
        s.close()
