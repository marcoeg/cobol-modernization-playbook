package banking

@JvmInline
value class Money(val cents: Long) {
    operator fun plus(o: Money) = Money(cents + o.cents)
    operator fun minus(o: Money) = Money(cents - o.cents)
    override fun toString(): String {
        val sign = if (cents < 0) "-" else ""
        val abs = kotlin.math.abs(cents)
        return "%s%d.%02d".format(sign, abs / 100, abs % 100)
    }
}
