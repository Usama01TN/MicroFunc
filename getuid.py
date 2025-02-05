# -*- coding: utf-8 -*-
"""
None
"""
try:
    from os import getuid
except:
    from ctypes import windll

    def getuid():
        return windll.shell32.IsUserAnAdmin() != 0
