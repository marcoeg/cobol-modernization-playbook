module banking
sig String{} sig Timestamp{}
sig Money { cents: Int }
enum Product { CHK, SAV }
enum Status { A, I, F }
enum Code   { DEPO, WDRW, FEEc, INTc, REVc }
sig Account {
  acctId: one String,
  status: one Status,
  product: one Product,
  currBal: one Money,
  odLimit: one Money
}
sig Txn {
  acctRef: one String,
  code: one Code,
  amount: one Money,
  ts: one Timestamp
}
pred WithinLimit[a: Account] { a.currBal.cents >= -a.odLimit.cents }
assert OverdraftPreserved { all a: Account | a.status in (A+F) implies WithinLimit[a] }
check OverdraftPreserved for 5 but 8 Int
