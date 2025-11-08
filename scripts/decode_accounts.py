#!/usr/bin/env python3
import sys, csv, os

REC_LEN = 58

def unpack_comp3(b: bytes) -> int:
    nibbles = []
    for byte in b:
        nibbles.append((byte >> 4) & 0xF)
        nibbles.append(byte & 0xF)
    sign = nibbles.pop()
    neg = (sign == 0xD)
    # Strip possible leading pad zeros
    digits = "".join(str(x) for x in nibbles).lstrip("0") or "0"
    val = int(digits)
    return -val if neg else val

def cents_to_str(n: int) -> str:
    sign = "-" if n < 0 else ""
    n = abs(n)
    return f"{sign}{n//100}.{n%100:02d}"

def decode_accounts(in_path: str):
    size = os.path.getsize(in_path)
    if size % REC_LEN != 0:
        print(f"WARNING: file size {size} is not a multiple of {REC_LEN}; trailing bytes will be ignored.", file=sys.stderr)
    records = []
    with open(in_path, "rb") as f:
        while True:
            chunk = f.read(REC_LEN)
            if len(chunk) < REC_LEN:
                break
            acct_id  = chunk[0:12].decode('ascii', errors='ignore').rstrip()
            cust_id  = chunk[12:24].decode('ascii', errors='ignore').rstrip()
            product  = chunk[24:28].decode('ascii', errors='ignore')
            status   = chunk[28:29].decode('ascii', errors='ignore')
            curr_bal = unpack_comp3(chunk[29:36])
            od_lim   = unpack_comp3(chunk[36:42])
            open_dt  = chunk[42:50].decode('ascii', errors='ignore')
            close_dt = chunk[50:58].decode('ascii', errors='ignore')
            records.append({
                "ACCT_ID": acct_id,
                "CUST_ID": cust_id,
                "PRODUCT": product,
                "STATUS": status,
                "CURR_BAL_CENTS": curr_bal,
                "CURR_BAL": cents_to_str(curr_bal),
                "OD_LIMIT_CENTS": od_lim,
                "OD_LIMIT": cents_to_str(od_lim),
                "OPEN_DATE": open_dt,
                "CLOSE_DATE": close_dt
            })
    return records

def main():
    if len(sys.argv) < 3:
        print("Usage: decode_accounts.py <input_dat> <output_csv>", file=sys.stderr)
        sys.exit(2)
    in_path, out_csv = sys.argv[1], sys.argv[2]
    recs = decode_accounts(in_path)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()) if recs else 
            ["ACCT_ID","CUST_ID","PRODUCT","STATUS","CURR_BAL_CENTS","CURR_BAL","OD_LIMIT_CENTS","OD_LIMIT","OPEN_DATE","CLOSE_DATE"])
        w.writeheader()
        for r in recs:
            w.writerow(r)
    print(f"Wrote {len(recs)} rows to {out_csv}")

if __name__ == "__main__":
    main()
