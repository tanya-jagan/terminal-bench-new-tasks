from pathlib import Path
username = "tb3testuser"
h = 0
for ch in username:
    h = ((h << 5) - h + ord(ch)) & 0xffffffff
powers = [pow(9, exp) for exp in range(19, -1, -1)]
result = None
for L in range(1, 0x10000):
    calc = (((L ^ h) ^ 0xa5f3) * 0x9e37) & 0xffffffff
    top16 = 0x3000 + (calc & 0xfff)
    n = (top16 << 48) | (h << 16) | L
    value = n
    digits = []
    for power in powers:
        digit = value // power
        if digit > 8:
            break
        digits.append(int(digit))
        value -= digit * power
    else:
        if value == 0 and len(digits) == 20:
            result = (L, h, top16, n, digits)
            break
if result:
    L, h, top16, n, digits = result
    sanitized = ''.join(str(d) for d in digits)
    key = '-'.join(sanitized[i:i+5] for i in range(0, 20, 5))
    print(key)
    print(hex(n))
else:
    print("no key found")
