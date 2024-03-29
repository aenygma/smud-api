import api
import pytest

def test_obj_creation():

    a = api.SMUD_API()
    assert a is not None

@pytest.mark.slow
def test_live_get_usage_by_day():
    """ get LIVE usage for a day """

    a = api.SMUD_API()
    a.login(api.config['Auth']['username'], api.config['Auth']['password'])
    date = (2019, 1, 1)

    data = a.get("cost", "day", date)
    assert type(data) is list
    if isinstance(data, list):
        assert len(data) > 0


