# encoding: utf-8
import functools


def show_info(msg, channel):
    print '%s: %s' % (channel, msg)


dbg = functools.partial(show_info, channel='dbg')
info = functools.partial(show_info, channel='info')

