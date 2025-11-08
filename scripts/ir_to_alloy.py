#!/usr/bin/env python3
import json, pathlib
ir = json.load(open("parsing/out/ir.json"))
out = []
def fact(s): out.append(s)
fact("fact WellTyped { all a: Account | a.odLimit.cents >= 0 }")
pathlib.Path("formal/alloy").mkdir(parents=True, exist_ok=True)
open("formal/alloy/facts.als","w").write("\n".join(out))
print("Wrote formal/alloy/facts.als")
