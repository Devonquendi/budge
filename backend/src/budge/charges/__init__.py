"""Pure domain logic: no database, no HTTP, no Akahu.

Everything in this package is a function of its arguments. That is deliberate —
these are the parts that decide what somebody owes, and the one place in a money
app where "probably" is not an acceptable answer. Keeping them free of I/O is
what makes them cheap to test exhaustively.
"""
