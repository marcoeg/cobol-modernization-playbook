#!/usr/bin/env python3
import json, os

IR = {
  "records": {
    "ACCOUNT": {
      "keys": ["ACCT-ID"],
      "fields": [
        {"name":"ACCT-ID","type":"string","len":12,"constraints":["notBlank"]},
        {"name":"CUST-ID","type":"string","len":12},
        {"name":"PRODUCT-CODE","type":"enum","domain":["CHK ","SAV "]},
        {"name":"ACCT-STATUS","type":"enum","domain":["A","I","F"]},
        {"name":"CURR-BAL","type":"decimal","scale":2,"signed":True},
        {"name":"OVERDRAFT-LIMIT","type":"decimal","scale":2,"signed":True},
        {"name":"OPEN-DATE","type":"date","fmt":"yyyyMMdd"},
        {"name":"CLOSE-DATE","type":"date","fmt":"yyyyMMdd","nullable":True}
      ]
    },
    "TXN": {
      "fields": [
        {"name":"ACCT-ID","type":"string","len":12},
        {"name":"TXN-ID","type":"string","len":16},
        {"name":"ORIG-TXN-ID","type":"string","len":16,"nullable":True},
        {"name":"TXN-CODE","type":"enum","domain":["DEPO","WDRW","FEE ","INT ","REV "]},
        {"name":"TXN-AMOUNT","type":"decimal","scale":2,"signed":True},
        {"name":"TXN-TS","type":"timestamp","fmt":"yyyyMMddHHmmss"},
        {"name":"CHANNEL","type":"enum","domain":["ATM ","BRCH","WEB ","ACH "]}
      ]
    }
  },
  "operations":[
    {
      "name":"APPLY-TXN",
      "pre": ["status(a) in {A,F} implies balance(a) >= -odLimit(a)"],
      "rules":[
        {"when":{"TXN-CODE":"DEPO"}, "effect":"BAL := BAL + AMT"},
        {"when":{"TXN-CODE":"WDRW"}, "guard":"BAL - AMT >= -ODLIM", "effect":"BAL := BAL - AMT", "else":"REJECT"},
        {"when":{"TXN-CODE":"FEE "}, "effect":"BAL := BAL + AMT"},
        {"when":{"TXN-CODE":"INT "}, "effect":"BAL := BAL + AMT"},
        {"when":{"TXN-CODE":"REV "}, "effect":"BAL := BAL - AMT"}
      ],
      "post": ["status(a) in {A,F} implies balance(a) >= -odLimit(a)"]
    }
  ],
  "batchFlow":[
    {"step":"read accounts sorted by ACCT-ID"},
    {"step":"merge-apply txns for TODAY sorted by (ACCT-ID, TS)"},
    {"step":"write updated accounts and exceptions"}
  ]
}

os.makedirs("parsing/out", exist_ok=True)
with open("parsing/out/ir.json","w") as f:
    json.dump(IR, f, indent=2)
print("Wrote parsing/out/ir.json")
