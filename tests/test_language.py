from scamscript import language
from scamscript.prompts import user_prompt

ENGLISH = "the call is about your account and you have to verify this with the bank today " * 2
SPANISH = "el banco le llama por su cuenta y usted tiene que verificar esto con la entidad hoy " * 2


def test_detects_english():
    assert language.detect(ENGLISH) == "en"


def test_detects_spanish():
    assert language.detect(SPANISH) == "es"


def test_short_text_unknown():
    assert language.detect("hola") == "unknown"


def test_instruction_override_and_unknown():
    assert "'es'" in language.instruction("es")
    assert "may not be English" in language.instruction(None)
    assert "may not be English" in language.instruction("unknown")


def test_prompt_carries_instruction():
    assert "may not be English" in user_prompt("a.txt", "x")
    assert "'es'" in user_prompt("a.txt", "x", "es")
