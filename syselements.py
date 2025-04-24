# -*- coding: utf-8 -*-
"""
None
"""
from os.path import join, expanduser, exists
from sys import platform


class DetectOS(object):
    """
    DetectOS class.
    """
    __osName = platform.lower()  # type: str

    @classmethod
    def isMobile(cls):
        """
        :return: bool
        """
        from platform import machine
        from os import environ
        import sys

        if platform.lower().startswith(('darwin', 'mac')) and cls.__osName in ["iphone", "ipad"]:
            return True
        elif hasattr(sys, 'getandroidapilevel') or 'ANDROID_BOOTLOGO' in environ or "aarch" in machine():
            cls.__osName = 'android'  # type: str
            return True
        return False

    @classmethod
    def osName(cls):
        """
        :return: str | unicode
        """
        cls.isMobile()
        return cls.__osName


isMobile = DetectOS.isMobile()  # type: bool
osName = DetectOS.osName()  # type: str


def createDesktopShortcut(shortcut_name, target_path, icon_path=None, arguments=None, exist_ok=True):
    """
    Create a desktop shortcut to an executable for Windows, macOS, or Linux.
    :param shortcut_name: (str | unicode) Name of the shortcut (without extension).
    :param target_path: (str | unicode) Full path to the executable.
    :param icon_path: (str | unicode | None) Optional path to an icon file.
    :param arguments: (str | unicode | None) Optional command-line arguments as a string.
    :param exist_ok: (bool)
    :return: bool
    """
    if not hasattr(arguments, 'encode'):
        arguments = ' '.join(arguments)  # type: str
    if isMobile:
        print("Unsupported platform:", osName)
        return False
    desktopPath = join(expanduser("~"), "Desktop")  # type: str
    if platform.lower().startswith(('win32', 'win64', 'windows')):
        link = join(desktopPath, shortcut_name + ".lnk")  # type: str
        if exists(link) and exist_ok:
            print("{} already exists".format(link))
            return False

        from ctypes import oledll, byref, sizeof, c_void_p, WINFUNCTYPE, HRESULT, c_wchar_p, c_int, cast, c_byte, \
            c_wchar_p
        from ctypes.wintypes import DWORD, LPCWSTR, BOOL
        from struct import Struct

        class _GUID(DWORD * 4):
            """
            _GUID class.
            """

            def __init__(self, guid):
                """
                :param guid: str | unicode
                """
                oledll.ole32.CLSIDFromString(guid, byref(self))

        class _PROPERTYKEY(DWORD * 5):
            """
            _PROPERTYKEY class.
            """

            def __init__(self, key, pid):
                """
                :param key: str | unicode
                :param pid: int
                """
                oledll.ole32.IIDFromString(key, byref(self))
                self[-1] = pid  # type: int

        _PropertyVariant = Struct("B7xP{}x".format(sizeof(c_void_p())))  # type: Struct
        _AppUserModelId = _PROPERTYKEY("{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}", 5)  # type: _PROPERTYKEY
        _CLSID_ShellLink = _GUID("{00021401-0000-0000-C000-000000000046}")  # type: _GUID
        _IID_IShellLinkW = _GUID("{000214F9-0000-0000-C000-000000000046}")  # type: _GUID
        _IID_IPersistFile = _GUID("{0000010B-0000-0000-C000-000000000046}")  # type: _GUID
        _IID_IPropertyStore = _GUID("{886d8eeb-8cf2-4446-8d02-cdba1dbdcf99}")  # type: _GUID
        _CLSCTX_INPROC_SERVER = 1  # type: int
        _COINIT_APARTMENTTHREADED = 2  # type: int
        _COINIT_DISABLE_OLE1DDE = 4  # type: int
        _VT_LPWSTR = 31  # type: int
        _CoCreateInstance = oledll.ole32.CoCreateInstance
        _QueryInterface = WINFUNCTYPE(HRESULT, _GUID, c_void_p)(0, "QueryInterface")  # type: WINFUNCTYPE
        _Release = WINFUNCTYPE(HRESULT)(2, "Release")  # type: WINFUNCTYPE
        _Save = WINFUNCTYPE(HRESULT, c_wchar_p, BOOL)(6, "Save")  # type: WINFUNCTYPE
        _SetPath = WINFUNCTYPE(HRESULT, c_wchar_p)(20, "SetPath")  # type: WINFUNCTYPE
        _SetArguments = WINFUNCTYPE(HRESULT, c_wchar_p)(12, "SetArguments")  # type: WINFUNCTYPE
        _SetDescription = WINFUNCTYPE(HRESULT, c_wchar_p)(7, "SetDescription")  # type: WINFUNCTYPE
        _SetIconLocation = WINFUNCTYPE(HRESULT, c_wchar_p, c_int)(17, "SetIconLocation")  # type: WINFUNCTYPE
        _SetValue = WINFUNCTYPE(HRESULT, c_void_p, c_void_p)(6, "SetValue")  # type: WINFUNCTYPE
        p_link = c_void_p()  # type: c_void_p
        p_file = c_void_p()  # type: c_void_p
        p_store = c_void_p()  # type: c_void_p
        p_app_id = LPCWSTR(shortcut_name)  # type: LPCWSTR
        oledll.ole32.CoInitializeEx(None, _COINIT_APARTMENTTHREADED | _COINIT_DISABLE_OLE1DDE)
        try:
            _CoCreateInstance(_CLSID_ShellLink, None, _CLSCTX_INPROC_SERVER, _IID_IShellLinkW, byref(p_link))
            _SetPath(p_link, c_wchar_p(target_path))
            if arguments:
                _SetArguments(p_link, c_wchar_p(arguments))
            _SetDescription(p_link, p_app_id)
            if icon_path:
                _SetIconLocation(p_link, c_wchar_p(icon_path), 0)
            _QueryInterface(p_link, _IID_IPropertyStore, byref(p_store))
            value = _PropertyVariant.pack(_VT_LPWSTR, cast(p_app_id, c_void_p).value)
            _SetValue(p_store, byref(_AppUserModelId), byref((c_byte * len(value))(*value)))
            _QueryInterface(p_link, _IID_IPersistFile, byref(p_file))
            _Save(p_file, c_wchar_p(link), True)
        finally:
            if p_file:
                _Release(p_file)
            if p_link:
                _Release(p_link)
            if p_store:
                _Release(p_store)
            oledll.ole32.CoUninitialize()
        return True
    elif platform.lower().startswith(('darwin', 'mac')):  # macOS
        from os import chmod

        link = join(desktopPath, shortcut_name + ".command")  # type: str
        if exists(link) and exist_ok:
            print("{} already exists".format(link))
            return False
        with open(link, 'w') as f:
            cmd = 'open "{}"'.format(target_path)  # type: str
            if arguments:
                cmd += ' --args ' + arguments  # type: str
            f.write('#!/bin/bash\n{}\n'.format(cmd))
        chmod(link, 0o755)
        return True
    elif platform.lower().startswith('linux'):
        from os import chmod

        link = join(desktopPath, shortcut_name + ".desktop")  # type: str
        if exists(link) and exist_ok:
            print("{} already exists".format(link))
            return False
        with open(link, 'w') as f:
            execLine = '"{}"'.format(target_path)  # type: str
            if arguments:
                execLine += ' ' + arguments  # type: str
            f.write("""[Desktop Entry]
Type=Application
Name={}
Exec={}
Icon={}
Terminal=false
""".format(shortcut_name, execLine, icon_path if icon_path else ''))
        chmod(link, 0o755)
        return True
    else:
        print("Unsupported platform:", platform)
        return False

# Example usage:
# createDesktopShortcut("MyApp", "/path/to/executable", "/path/to/icon.ico or .png", "--arg1 value1 --arg2 value2")
