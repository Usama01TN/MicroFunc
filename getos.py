# -*- coding: utf-8 -*-
"""
None
"""
# For platform class.
from platform import system, machine
from os import environ
import sys


class DetectOS(object):
    __osName = system().lower()

    @staticmethod
    def isMobile():
        """
        :return: bool
        """
        if system().lower().startswith("darwin") and DetectOS.__osName in ["iphone", "ipad"]:
            DetectOS.__osName = 'ios'  # type str
            return True
        elif hasattr(sys, 'getandroidapilevel') or 'ANDROID_BOOTLOGO' in environ or "aarch" in machine():
            DetectOS.__osName = 'android'  # type str
            return True
        return False

    @staticmethod
    def osName():
        """
        :return: str | unicode
        """
        DetectOS.isMobile()
        return DetectOS.__osName
