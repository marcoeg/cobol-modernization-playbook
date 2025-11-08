package banking

import java.io.File
import java.nio.charset.StandardCharsets

const val ACCT_REC_LEN = 58
const val TXN_REC_LEN = 72

fun unpackComp3(bytes: ByteArray): Long {
    val nibbles = ArrayList<Int>(bytes.size * 2)
    for (b in bytes) {
        nibbles.add((b.toInt() ushr 4) and 0xF)
        nibbles.add(b.toInt() and 0xF)
    }
    val sign = nibbles.removeAt(nibbles.lastIndex)
    val neg = (sign == 0xD)
    val digits = nibbles.joinToString("") { it.toString() }.trimStart('0').ifEmpty { "0" }
    val v = digits.toLong()
    return if (neg) -v else v
}

fun packComp3Fixed(valueCents: Long, totalDigits: Int): ByteArray {
    val neg = valueCents < 0
    val s = kotlin.math.abs(valueCents).toString().padStart(totalDigits, '0')
    val nibbles = ArrayList<Int>(s.length + 1)
    for (ch in s) nibbles.add(ch - '0')
    nibbles.add(if (neg) 0xD else 0xC)
    if (nibbles.size % 2 == 1) nibbles.add(0, 0)
    val out = ByteArray(nibbles.size / 2)
    var j = 0
    for (i in out.indices) {
        out[i] = (((nibbles[j] shl 4) or (nibbles[j + 1] and 0xF))).toByte()
        j += 2
    }
    return out
}

private fun String.asciiFixed(n: Int) =
    this.toByteArray(StandardCharsets.US_ASCII).copyOf(n).also { if (it.size < n) it.fill(32, it.size, n) }

private fun readAscii(b: ByteArray, from: Int, to: Int) =
    String(b, from, to - from, StandardCharsets.US_ASCII).trimEnd()

data class AccountRec(
    var acctId: String,
    var custId: String,
    var product: String,
    var status: String,
    var currBal: Money,
    var odLimit: Money,
    var openDate: Int,
    var closeDate: Int
)

data class TxnRec(
    val acctId: String,
    val txnId: String,
    val origId: String,
    val code: String,
    val amount: Money,
    val ts: Long,
    val channel: String,
    val raw: ByteArray? = null
)

fun readAccounts(path: String): MutableList<AccountRec> {
    val f = File(path)
    val out = mutableListOf<AccountRec>()
    f.inputStream().use { ins ->
        val buf = ByteArray(ACCT_REC_LEN)
        while (true) {
            val n = ins.readNBytes(buf, 0, ACCT_REC_LEN)
            if (n < ACCT_REC_LEN) break
            val acctId = readAscii(buf, 0, 12)
            val custId = readAscii(buf, 12, 24)
            val product = String(buf, 24, 4, StandardCharsets.US_ASCII)
            val status = String(buf, 28, 1, StandardCharsets.US_ASCII)
            val currBal = unpackComp3(buf.copyOfRange(29, 36))
            val odLimit = unpackComp3(buf.copyOfRange(36, 42))
            val openDt = String(buf, 42, 8, StandardCharsets.US_ASCII).toInt()
            val closeDt = String(buf, 50, 8, StandardCharsets.US_ASCII).toInt()
            out += AccountRec(acctId, custId, product, status, Money(currBal), Money(odLimit), openDt, closeDt)
        }
    }
    return out
}

fun readTxns(path: String): MutableList<TxnRec> {
    val f = File(path)
    val out = mutableListOf<TxnRec>()
    f.inputStream().use { ins ->
        val buf = ByteArray(TXN_REC_LEN)
        while (true) {
            val n = ins.readNBytes(buf, 0, TXN_REC_LEN)
            if (n < TXN_REC_LEN) break
            val acctId = readAscii(buf, 0, 12)
            val txnId = readAscii(buf, 12, 28)
            val origId = readAscii(buf, 28, 44)
            val code = String(buf, 44, 4, StandardCharsets.US_ASCII)
            val amount = unpackComp3(buf.copyOfRange(48, 54))
            val ts = String(buf, 54, 14, StandardCharsets.US_ASCII).toLong()
            val ch = String(buf, 68, 4, StandardCharsets.US_ASCII)
            out += TxnRec(acctId, txnId, origId, code, Money(amount), ts, ch, buf.copyOf())
        }
    }
    return out
}

fun writeAccounts(path: String, accounts: List<AccountRec>) {
    File(path).parentFile?.mkdirs()
    File(path).outputStream().use { out ->
        for (a in accounts) {
            val rec = ByteArray(ACCT_REC_LEN)
            System.arraycopy(a.acctId.asciiFixed(12), 0, rec, 0, 12)
            System.arraycopy(a.custId.asciiFixed(12), 0, rec, 12, 12)
            System.arraycopy(a.product.asciiFixed(4), 0, rec, 24, 4)
            System.arraycopy(a.status.asciiFixed(1), 0, rec, 28, 1)
            System.arraycopy(packComp3Fixed(a.currBal.cents, 13), 0, rec, 29, 7)
            System.arraycopy(packComp3Fixed(a.odLimit.cents, 11), 0, rec, 36, 6)
            "%08d".format(a.openDate).toByteArray(StandardCharsets.US_ASCII).copyOf(8).also {
                System.arraycopy(it, 0, rec, 42, 8)
            }
            "%08d".format(a.closeDate).toByteArray(StandardCharsets.US_ASCII).copyOf(8).also {
                System.arraycopy(it, 0, rec, 50, 8)
            }
            require(rec.size == ACCT_REC_LEN)
            out.write(rec)
        }
    }
}

fun writeExceptions(path: String, exceptions: List<TxnRec>) {
    File(path).parentFile?.mkdirs()
    File(path).outputStream().use { out ->
        for (t in exceptions) {
            val rec = ByteArray(TXN_REC_LEN)
            System.arraycopy(t.acctId.asciiFixed(12), 0, rec, 0, 12)
            System.arraycopy(t.txnId.asciiFixed(16), 0, rec, 12, 16)
            System.arraycopy(t.origId.asciiFixed(16), 0, rec, 28, 16)
            System.arraycopy(t.code.asciiFixed(4), 0, rec, 44, 4)
            System.arraycopy(packComp3Fixed(t.amount.cents, 11), 0, rec, 48, 6)
            "%014d".format(t.ts).toByteArray(StandardCharsets.US_ASCII).copyOf(14).also {
                System.arraycopy(it, 0, rec, 54, 14)
            }
            System.arraycopy(t.channel.asciiFixed(4), 0, rec, 68, 4)
            require(rec.size == TXN_REC_LEN)
            out.write(rec)
        }
    }
}
