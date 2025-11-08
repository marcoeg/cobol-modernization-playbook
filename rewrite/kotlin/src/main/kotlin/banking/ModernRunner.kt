package banking

import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption

fun main() {
    val accIn = "data/accounts.dat"
    val txnIn = "data/txns.dat"
    val outDir = File("out").apply { mkdirs() }
    val artDir = File("tests/artifacts").apply { mkdirs() }

    require(File(accIn).exists() && File(txnIn).exists()) {
        "Missing inputs in data/ (accounts.dat, txns.dat)"
    }

    val accounts = readAccounts(accIn)
    val txns = readTxns(txnIn)

    val (accOut, exc) = runPosting(accounts, txns)

    val outAccModern = "out/accounts_out_modern.dat"
    val outExcModern = "out/exceptions_modern.dat"

    writeAccounts(outAccModern, accOut)
    writeExceptions(outExcModern, exc)

    Files.copy(
        File(outAccModern).toPath(),
        File("tests/artifacts/accounts_out_modern.dat").toPath(),
        StandardCopyOption.REPLACE_EXISTING
    )

    println("Modern Kotlin runner complete:")
    println(" - $outAccModern")
    println(" - $outExcModern")
    println(" - tests/artifacts/accounts_out_modern.dat")
}
