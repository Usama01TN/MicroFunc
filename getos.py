# -*- coding: utf-8 -*-
"""
None
"""
# For platform class
from platform import system, machine
from os import environ
import sys


class DetectOS(object):
    __osName = system().lower()

    @classmethod
    def isMobile(cls):
        if system().lower().startswith("darwin") and cls.__osName in ["iphone", "ipad"]:
            cls.__osName = 'ios'
            return True
        elif hasattr(sys, 'getandroidapilevel') or 'ANDROID_BOOTLOGO' in environ or "aarch" in machine():
            cls.__osName = 'android'
            return True
        return False

    @classmethod
    def osName(cls):
        cls.isMobile()
        return cls.__osName
