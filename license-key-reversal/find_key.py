username = "tb3testuser"
h = 0
for ch in username:
    h = ((h << 5) - h + ord(ch)) & 0xffffffff
pow36 = [pow(36, exp) for exp in range(19, -1, -1)]
result = None
for L in range(1, 0x10000):
    calc = (((L ^ h) ^ 0xa5f3) * 0x9e37) & 0xffffffff
    top16 = 0x3000 + (calc & 0xfff)
    n = (top16 << 48) | (h << 16) | L
    value = n
    digits = []
    for power in pow36:
        digit = value // power
        digits.append(int(digit))
        value -= digit * power
    if value != 0:
        continue
    sanitized_chars = []
    for d in digits:
        if d < 10:
            sanitized_chars.append(str(d))
        else:
            sanitized_chars.append(chr(ord('A') + d - 10))
    key = '-'.join(''.join(sanitized_chars[i:i+5]) for i in range(0, 20, 5))
    if len(key.replace('-', '')) != 20:
        continue
    result = (L, h, top16, n, key)
    break
if result:
    L, h, top16, n, key = result
    print(key)
    print(hex(n))
else:
    print("not found")
