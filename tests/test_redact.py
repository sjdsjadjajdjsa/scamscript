from scamscript.redact import describe, redact


def test_masks_email():
    text, counts = redact("write to alan.reyes@example.com now")
    assert text == "write to a***@example.com now"
    assert counts == {"email": 1}


def test_masks_card_keeping_last_four():
    text, counts = redact("card 4111 1111 1111 1234 expiring")
    assert "4111" not in text
    assert "1234" in text
    assert counts == {"card": 1}


def test_masks_ssn():
    text, _ = redact("ssn 447-12-9981 on file")
    assert text == "ssn ***-**-9981 on file"


def test_masks_phone_keeping_last_two():
    text, counts = redact("call +1 415 555 0142 back")
    assert "0142" not in text
    assert text.endswith("42 back")
    assert counts["phone"] == 1


def test_masks_long_digits():
    text, counts = redact("reference 20044719981 here")
    assert "2004471" not in text
    assert text.endswith("9981 here")
    assert counts["digits"] == 1


def test_keeps_short_ids():
    text, counts = redact("case RE-8814 and year 2026")
    assert text == "case RE-8814 and year 2026"
    assert counts == {}


def test_multiple_hits_counted():
    _, counts = redact("a@b.co and c@d.co")
    assert counts == {"email": 2}


def test_describe():
    assert describe({}) == "no identifiers matched"
    assert describe({"card": 2}) == "card=2"


def test_redact_is_idempotent_on_masked_text():
    once, _ = redact("card 4111 1111 1111 1234")
    twice, _ = redact(once)
    assert once == twice
