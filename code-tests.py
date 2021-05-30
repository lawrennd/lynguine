#!/usr/bin/env python

import nose, warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    nose.main("ndlpy", defaultTest="ndlpy/tests", argv=["", ""])
