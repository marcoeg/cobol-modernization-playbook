package banking

const val TODAY = 20250101

private fun yyyymmddFromTs(ts: Long): Int = (ts / 1_000_000L).toInt()

fun runPosting(accounts: MutableList<AccountRec>, txns: MutableList<TxnRec>): Pair<List<AccountRec>, List<TxnRec>> {
    accounts.sortBy { it.acctId }
    txns.sortWith(compareBy<TxnRec>({ it.acctId }, { it.ts }, { it.txnId }))

    val exceptions = mutableListOf<TxnRec>()
    var ti = 0
    for (a in accounts) {
        while (ti < txns.size && txns[ti].acctId < a.acctId) ti++
        while (ti < txns.size && txns[ti].acctId == a.acctId) {
            val t = txns[ti]
            if (yyyymmddFromTs(t.ts) == TODAY) {
                when (t.code) {
                    "DEPO", "FEE ", "INT " -> a.currBal = a.currBal + t.amount
                    "REV " -> a.currBal = a.currBal - t.amount
                    "WDRW" -> {
                        val next = a.currBal - t.amount
                        val negLimit = Money(0 - a.odLimit.cents)
                        if (next.cents >= negLimit.cents) a.currBal = next else exceptions += t
                    }
                }
            }
            ti++
        }
    }
    return accounts to exceptions
}
