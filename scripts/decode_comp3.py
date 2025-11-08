#!/usr/bin/env python3
import sys
def unpack_comp3(b):
    nibbles = []
    for byte in b:
        nibbles.append((byte >> 4) & 0xF)
        nibbles.append(byte & 0xF)
    sign = nibbles.pop()
    neg = (sign == 0xD)
    digits = "".join(str(x) for x in nibbles).lstrip("0") or "0"
    return (-1 if neg else 1) * int(digits)
rec = open(sys.argv[1], "rb").read(58)
acct_id = rec[0:12].decode().rstrip()
curr_bal = unpack_comp3(rec[29:36])
od_lim = unpack_comp3(rec[36:42])
print(acct_id, curr_bal, od_lim)
