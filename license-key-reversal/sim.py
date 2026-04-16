username = "tb3testuser"

def compute_hash(username):
    h = 0
    for ch in username:
        h = ((h << 5) - h + ord(ch)) & 0xffffffff
    return h


def validate(username, key):
    h = compute_hash(username)
    sanitized = key.upper().replace('-', '')
    if len(sanitized) != 20:
        return False
    allowed = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if any(ch not in allowed for ch in sanitized):
        return False
    n = 0
    for ch in sanitized:
        if '0' <= ch <= '9':
            digit = ord(ch) - ord('0')
        else:
            digit = ord(ch) - 0x37
        n = n * 9 + digit
    if (n >> 60) != 3:
        return False
    if ((n >> 16) & 0xffffffff) != h:
        return False
    L = n & 0xffff
    if L == 0:
        return False
    calc = (((L ^ h) ^ 0xa5f3) * 0x9e37) & 0xffffffff
    top16 = (n >> 48) & 0xffff
    if ((top16 ^ calc) & 0xfff) != 0:
        return False
    return True

key = "33408-12814-04757-36483"
print("hash", hex(compute_hash(username)))
print("simulate valid?", validate(username, key))
