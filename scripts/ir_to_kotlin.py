#!/usr/bin/env python3
import json, pathlib
ir = json.load(open("parsing/out/ir.json"))
kt = []
kt.append("""package banking
@JvmInline value class Money(val cents: Long) {
  operator fun plus(o: Money) = Money(cents + o.cents)
  operator fun minus(o: Money) = Money(cents - o.cents)
}
enum class Status { A, I, F }
enum class Product { CHK, SAV }
enum class Code { DEPO, WDRW, FEE, INT, REV }
data class Account(var acctId: String, var status: Status, var product: Product, var currBal: Money, var odLimit: Money)
data class Txn(val acctRef: String, val code: Code, val amount: Money)
fun applyTxn(a: Account, t: Txn): Boolean {
  return when (t.code) {
    Code.DEPO, Code.FEE, Code.INT -> { a.currBal = a.currBal + t.amount; true }
    Code.REV -> { a.currBal = a.currBal - t.amount; true }
    Code.WDRW -> {
      val next = a.currBal - t.amount
      if (next.cents >= -a.odLimit.cents) { a.currBal = next; true } else false
    }
  }
}
""")
pathlib.Path("rewrite/kotlin").mkdir(parents=True, exist_ok=True)
open("rewrite/kotlin/Generated.kt","w").write("\n".join(kt))
print("Wrote rewrite/kotlin/Generated.kt")
