#!/usr/bin/env python3
import sys, csv, subprocess, os, tempfile

def read_csv(path):
    rows = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows[row["ACCT_ID"]] = row
    return rows

def main():
    if len(sys.argv) < 4:
        print("Usage: compare_accounts.py <legacy_dat> <modern_dat> <out_dir>", file=sys.stderr)
        sys.exit(2)
    legacy_dat, modern_dat, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    # decode both to CSV using sibling decoder
    decoder = os.path.join(os.path.dirname(__file__), "decode_accounts.py")
    legacy_csv = os.path.join(out_dir, "accounts_out_legacy.csv")
    modern_csv = os.path.join(out_dir, "accounts_out_modern.csv")
    subprocess.check_call([decoder, legacy_dat, legacy_csv])
    subprocess.check_call([decoder, modern_dat, modern_csv])

    L = read_csv(legacy_csv)
    M = read_csv(modern_csv)

    diff_csv = os.path.join(out_dir, "diff_accounts.csv")
    fields = ["ACCT_ID","FIELD","LEGACY","MODERN","EQUAL"]
    diffs = 0
    with open(diff_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        keys = sorted(set(L.keys()) | set(M.keys()))
        for k in keys:
            l = L.get(k); m = M.get(k)
            if l is None or m is None:
                diffs += 1
                w.writerow({"ACCT_ID": k, "FIELD":"__presence__", "LEGACY": "present" if l else "missing", "MODERN": "present" if m else "missing", "EQUAL":"NO"})
                continue
            for field in ["STATUS","CURR_BAL","OD_LIMIT"]:
                eq = (l.get(field) == m.get(field))
                if not eq:
                    diffs += 1
                w.writerow({"ACCT_ID": k, "FIELD": field, "LEGACY": l.get(field,""), "MODERN": m.get(field,""), "EQUAL": "YES" if eq else "NO"})

    summary = os.path.join(out_dir, "diff_summary.txt")
    with open(summary, "w") as f:
        f.write(f"Compared {len(L)} legacy accounts to {len(M)} modern accounts\n")
        f.write(f"Differences: {diffs}\n")
        f.write(f"Details: {diff_csv}\n")
    print(open(summary).read())

if __name__ == "__main__":
    main()
