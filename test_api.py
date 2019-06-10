#!/usr/bin/env python -m pytest

# notes: invoke ./test_api.py
#  else complains of importerrors on bs4

import api
import pytest

class Test_API:

    def test_obj_creation(self):

        a = api.SMUD_API()
        assert a is not None

    @pytest.mark.slow
    def test_live_get_usage_by_day(self):
        """ get LIVE usage for a day """

        a = api.SMUD_API()
        a.login(api.config['Auth']['username'], api.config['Auth']['password'])
        date = (2019, 1, 1)

        data = a.get("cost", "day", date)
        assert type(data) is list


