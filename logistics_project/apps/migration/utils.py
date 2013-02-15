#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.utils.functional import curry
# from rapidsms.contrib.ajax.utils import call_router

# TODO: fix
call_router = lambda: None
# these helper methods are just proxies to app.py
send_test_message = curry(call_router, "migration", "send")
check_status = curry(call_router, "migration", "status")
