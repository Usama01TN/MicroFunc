# coding=utf-8
"""
Resolves any Python text encoding
"""


def ioWrite(fl, text='', mode='w', encoding='utf-8'):
    try:
        with open(fl, mode, encoding=encoding) as wf:
            wf.write(text)
    except TypeError:
        try:
            import io
            with io.open(fl, mode, encoding=encoding) as wf:
                wf.write(text)
        except TypeError:
            with open(fl, mode) as wf:
                wf.write(text)


def ioOpenRead(fl, encoding='utf-8'):
    try:
        return open(fl, 'r')
    except UnicodeDecodeError:
        try:
            return open(fl, 'rb')
        except:
            try:
                return open(fl, 'r', encoding=encoding)
            except TypeError:
                import io

                try:
                    return io.open(fl, 'r', encoding=encoding)
                except:
                    return io.open(fl, 'rb', encoding=encoding)
