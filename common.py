# encoding: utf-8
import functools

switches = {
    'dbg': True
}


def show_info(msg, channel):
    if switches[channel]:
        print '%s: %s' % (channel, msg)


dbg = functools.partial(show_info, channel='dbg')
info = functools.partial(show_info, channel='info')

