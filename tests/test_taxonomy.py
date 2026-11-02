import pytest

from scamscript.taxonomy import SLUGS, label, parse_filter, slugify


@pytest.mark.parametrize(
    "text,slug",
    [
        ("government impersonation vishing (tax/revenue)", "gov-impersonation"),
        ("vishing (automated robocall payment scam)", "vishing"),
        ("romance scam / smishing long con", "romance"),
        ("romance scam, pig-butchering-adjacent", "romance"),
        ("parcel delivery fee scam", "delivery"),
        ("tech support scam with remote access", "tech-support"),
        ("business email compromise by phone", "bec"),
        ("crypto investment", "crypto"),
        ("pig butchering investment scam", "investment"),
        ("Medicare old age benefits", "gov-impersonation"),
        ("Social Security suspension", "gov-impersonation"),
        ("student loan debt relief", "refund"),
        ("interest rate reduction", "refund"),
        ("smishing text message", "smishing"),
        ("utility impersonation", "utility"),
        ("utility rebate robocall", "utility"),
        ("something entirely new", "other"),
        ("", "other"),
    ],
)
def test_mapping(text, slug):
    assert slugify(text) == slug


def test_bec_wins_over_vishing():
    assert slugify("vishing-led wire fraud, business email compromise") == "bec"


def test_case_and_punctuation_insensitive():
    assert slugify("TECH-SUPPORT, remote access!") == "tech-support"


def test_slugs_are_closed_set():
    assert "other" in SLUGS and "vishing" in SLUGS
    assert slugify("nonsense") in SLUGS


def test_parse_filter_accepts_comma_and_spaces():
    assert parse_filter(["tech support,romance", "vishing"]) == {
        "tech-support",
        "romance",
        "vishing",
    }
    assert parse_filter(None) == set()


def test_label_known_and_fallback():
    assert label("bec") == "Business email compromise"
    assert label("odd") == "odd"


@pytest.mark.parametrize(
    "texts,channel",
    [
        (("USPS delivery smishing text",), "smishing"),
        (("phone robocall",), "vishing"),
        (("vendor invoice", "email"), "email"),
        (("something",), "other"),
        (("first", "second"), "other"),
    ],
)
def test_channel_of(texts, channel):
    from scamscript.taxonomy import channel_of

    assert channel_of(*texts) == channel


def test_channel_matching_uses_word_boundaries():
    from scamscript.taxonomy import channel_of

    assert channel_of("rainfall") == "other"
