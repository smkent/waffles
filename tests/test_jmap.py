import jmapc

from wafflesbot.jmap import JMAPClientWrapper


def test_client() -> None:
    c = JMAPClientWrapper.create_with_api_token(
        host="jmap-api.example.net",
        api_token="ness__pk_fire",
    )
    assert isinstance(c, jmapc.Client)
