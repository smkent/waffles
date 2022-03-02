import jmapc

from wafflesbot.jmap import JMAPClientWrapper


def test_client() -> None:
    c = JMAPClientWrapper(
        host="jmap-api.example.net", user="ness", password="pk_fire"
    )
    assert isinstance(c, jmapc.Client)
