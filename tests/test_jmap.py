import jmapc

from wafflesbot.jmap import JMAPClientWrapper


def test_client() -> None:
    c = JMAPClientWrapper.create_with_api_token(
        host="jmap-api.example.net",
        api_token="ness__pk_fire",
        mailbox_name="pigeonhole",
        new_email_callback=lambda email: None,
    )
    assert isinstance(c, jmapc.Client)
