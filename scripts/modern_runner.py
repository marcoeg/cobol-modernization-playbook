#!/usr/bin/env python3
"""Modern Python runner for the COBOL daily posting slice.

Reads fixed-width binary input files with COMP-3 decimals:
 - data/accounts.dat  (58-byte records)
 - data/txns.dat      (72-byte records)

Applies the same rules as DAILYPOST.cbl and writes outputs:
 - out/accounts_out_modern.dat       (58-byte records, same layout as input accounts)
 - out/exceptions_modern.dat         (72-byte records, same layout as input txns)
Also copies accounts_out_modern.dat to:
 - tests/artifacts/accounts_out_modern.dat  (so 'make gm-diff' can compare)

Usage (from repo root):
  python3 scripts/modern_runner.py
"""
import os
from typing import List, Dict, Tuple

# ---- Fixed layout constants ----
ACCT_REC_LEN = 58
TXN_REC_LEN  = 72

TODAY = 20250101  # keep aligned with the COBOL slice

# ---- COMP-3 helpers ----
def unpack_comp3(b: bytes) -> int:
    """Unpack packed-decimal (COMP-3) into an integer of cents."""
    nibbles = []
    for byte in b:
        nibbles.append((byte >> 4) & 0xF)
        nibbles.append(byte & 0xF)
    sign = nibbles.pop()
    neg = (sign == 0xD)
    digits = "".join(str(x) for x in nibbles).lstrip("0") or "0"
    val = int(digits)
    return -val if neg else val

def pack_comp3_fixed(value_cents: int, total_digits: int) -> bytes:
    """Pack an integer into COMP-3 with a fixed number of digits and sign nibble."""
    neg = value_cents < 0
    s = str(abs(value_cents)).rjust(total_digits, '0')
    nibbles = [int(d) for d in s]
    nibbles.append(0x0D if neg else 0x0C)
    if len(nibbles) % 2 == 1:
        nibbles = [0] + nibbles
    out = bytearray()
    for i in range(0, len(nibbles), 2):
        out.append((nibbles[i] << 4) | (nibbles[i+1] & 0x0F))
    return bytes(out)

# ---- Parsers ----
def read_accounts(path: str) -> List[dict]:
    accs = []
    with open(path, 'rb') as f:
        while True:
            rec = f.read(ACCT_REC_LEN)
            if len(rec) < ACCT_REC_LEN:
                break
            acc = {
                "ACCT_ID":    rec[0:12].decode('ascii', 'ignore').rstrip(),
                "CUST_ID":    rec[12:24].decode('ascii', 'ignore').rstrip(),
                "PRODUCT":    rec[24:28].decode('ascii', 'ignore'),
                "STATUS":     rec[28:29].decode('ascii', 'ignore'),
                "CURR_BAL":   unpack_comp3(rec[29:36]),       # cents
                "OD_LIMIT":   unpack_comp3(rec[36:42]),       # cents
                "OPEN_DATE":  int(rec[42:50].decode('ascii', 'ignore') or "0"),
                "CLOSE_DATE": int(rec[50:58].decode('ascii', 'ignore') or "0"),
            }
            accs.append(acc)
    return accs

def read_txns(path: str) -> List[dict]:
    txns = []
    with open(path, 'rb') as f:
        while True:
            rec = f.read(TXN_REC_LEN)
            if len(rec) < TXN_REC_LEN:
                break
            t = {
                "ACCT_ID":   rec[0:12].decode('ascii', 'ignore').rstrip(),
                "TXN_ID":    rec[12:28].decode('ascii', 'ignore').rstrip(),
                "ORIG_ID":   rec[28:44].decode('ascii', 'ignore').rstrip(),
                "CODE":      rec[44:48].decode('ascii', 'ignore'),
                "AMOUNT":    unpack_comp3(rec[48:54]),             # cents
                "TS":        int(rec[54:68].decode('ascii', 'ignore') or "0"),  # yyyymmddHHMMSS
                "CHANNEL":   rec[68:72].decode('ascii', 'ignore'),
                "RAW":       rec,  # keep original raw bytes for exception writeback
            }
            txns.append(t)
    return txns

# ---- Writers ----
def write_accounts(path: str, accs: List[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        for a in accs:
            # rebuild record in the exact same layout
            out = bytearray()
            out += a['ACCT_ID'].encode('ascii')[:12].ljust(12, b' ')
            out += a['CUST_ID'].encode('ascii')[:12].ljust(12, b' ')
            out += a['PRODUCT'].encode('ascii')[:4].ljust(4, b' ')
            out += a['STATUS'].encode('ascii')[:1].ljust(1, b' ')
            out += pack_comp3_fixed(a['CURR_BAL'], 13)   # S9(11)V99 -> 13 digits incl 2 decimals
            out += pack_comp3_fixed(a['OD_LIMIT'], 11)   # S9(9)V99  -> 11 digits incl 2 decimals
            out += f"{a['OPEN_DATE']:08d}".encode('ascii')
            out += f"{a['CLOSE_DATE']:08d}".encode('ascii')
            assert len(out) == ACCT_REC_LEN
            f.write(out)

def write_exceptions(path: str, exceptions: List[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        for t in exceptions:
            # write same layout as input TXN
            out = bytearray()
            out += t['ACCT_ID'].encode('ascii')[:12].ljust(12, b' ')
            out += t['TXN_ID'].encode('ascii')[:16].ljust(16, b' ')
            out += t['ORIG_ID'].encode('ascii')[:16].ljust(16, b' ')
            out += t['CODE'].encode('ascii')[:4].ljust(4, b' ')
            out += pack_comp3_fixed(t['AMOUNT'], 11)     # S9(9)V99 -> 11 digits
            out += f"{t['TS']:014d}".encode('ascii')
            out += t['CHANNEL'].encode('ascii')[:4].ljust(4, b' ')
            assert len(out) == TXN_REC_LEN
            f.write(out)

# ---- Core posting logic ----
def yyyymmdd_from_ts(ts: int) -> int:
    return ts // 1000000  # integer division

def run_posting(accounts: List[dict], txns: List[dict]) -> Tuple[List[dict], List[dict]]:
    # Sort inputs to mimic merge pattern in COBOL
    accounts = sorted(accounts, key=lambda a: a['ACCT_ID'])
    txns = sorted(txns, key=lambda t: (t['ACCT_ID'], t['TS'], t['TXN_ID']))

    exc: List[dict] = []
    ti = 0
    for a in accounts:
        # consume all txns matching current account (while maintaining pointer)
        while ti < len(txns) and txns[ti]['ACCT_ID'] < a['ACCT_ID']:
            ti += 1
        while ti < len(txns) and txns[ti]['ACCT_ID'] == a['ACCT_ID']:
            t = txns[ti]
            # date filter same as COBOL: only apply if TS(1:8) == TODAY
            if yyyymmdd_from_ts(t['TS']) == TODAY:
                code = t['CODE']
                if code == 'DEPO' or code == 'FEE ' or code == 'INT ':
                    a['CURR_BAL'] += t['AMOUNT']
                elif code == 'REV ':
                    a['CURR_BAL'] -= t['AMOUNT']
                elif code == 'WDRW':
                    new_bal = a['CURR_BAL'] - t['AMOUNT']
                    neg_limit = 0 - a['OD_LIMIT']
                    if new_bal >= neg_limit:
                        a['CURR_BAL'] = new_bal
                    else:
                        exc.append(t)
                else:
                    # unknown code: ignore (or collect as exception if desired)
                    pass
            ti += 1
    return accounts, exc

def main():
    # paths
    acc_in = "data/accounts.dat"
    txn_in = "data/txns.dat"
    out_dir = "out"
    art_dir = "tests/artifacts"

    if not os.path.exists(acc_in) or not os.path.exists(txn_in):
        raise SystemExit("ERROR: missing input files in data/ (accounts.dat, txns.dat)")

    accs = read_accounts(acc_in)
    txns = read_txns(txn_in)
    accs_out, exceptions = run_posting(accs, txns)

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(art_dir, exist_ok=True)
    out_acc_modern = os.path.join(out_dir, "accounts_out_modern.dat")
    out_exc_modern = os.path.join(out_dir, "exceptions_modern.dat")
    write_accounts(out_acc_modern, accs_out)
    write_exceptions(out_exc_modern, exceptions)

    # Copy to comparator expected location
    import shutil
    shutil.copyfile(out_acc_modern, os.path.join(art_dir, "accounts_out_modern.dat"))

    print("Modern runner complete:")
    print(" -", out_acc_modern)
    print(" -", out_exc_modern)
    print(" - tests/artifacts/accounts_out_modern.dat (for gm-diff)")

if __name__ == "__main__":
    main()
