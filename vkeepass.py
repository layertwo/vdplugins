#!/usr/bin/env python3
"""
KeePass (.kdbx) reader for VisiData

Dive through KeePass group and copy passwords to clipboard

TODO:
- Edit and save back to .kdbx
- Default password field hide (not column) // maybe vd feature?
"""
from visidata import *

__name__ = 'vkeepass'
__author__ = 'Lucas Messenger @layertwo'
__version__ = '0.1'


def copy_password(val):
    result = vd().input('copy password? [Y/n]: ')
    if result.lower() == 'y':
        import pyperclip
        pyperclip.copy(val)
        vd.status('copied password!')


def unlock_kp():
    sheet = vd().sheet
    sheet.password = vd().input('kdbx password: ', display=False)
    sheet.reload()


def read_kp(source, password):
    from pykeepass import PyKeePass
    from pykeepass.exceptions import CredentialsIntegrityError
    try:
        return PyKeePass(source, password=password)
    except CredentialsIntegrityError:
        vd.status('unable to unlock kdbx. use ^N to enter password', priority=3)
        return []


class KeePassGroupSheet(Sheet):
    """
    KeePassGroupSheet representing a KeePass group
    """
    rowtype = 'passwords'
    columns = [
       ColumnAttr('title', type=str, width=20),
       ColumnAttr('username', type=str, width=20),
       ColumnAttr('password', type=str, display=False, width=20),
       ColumnAttr('url', type=str, width=20),
       ColumnAttr('notes', type=str, width=20),
       ColumnAttr('expired', type=bool, width=20),
       ColumnAttr('expires', type=date, fmtstr='%Y-%m-%d %H:%M:%S', width=20),
       ColumnAttr('created', 'ctime', type=date, fmtstr='%Y-%m-%d %H:%M:%S', width=20),
       ColumnAttr('accessed', 'atime', type=date, fmtstr='%Y-%m-%d %H:%M:%S', width=20),
       ColumnAttr('modtime', 'mtime', type=date, fmtstr='%Y-%m-%d %H:%M:%S', width=20),
    ]
    @property
    def entries(self):
        return len(self.source.entries)

    def iterload(self):
        for pw in Progress(self.source.entries):
            yield pw


class KeePassIndexSheet(Sheet):
    """
    KeePassIndexSheet representing KeePass groups
    """
    rowtype = 'groups'
    columns = [
        ColumnAttr('name', type=str, width=20),
        ColumnAttr('entries', type=int, width=20),
        ColumnAttr('expires', 'source.expires', type=date, fmtstr='%Y-%m-%d %H:%M:%S', width=20),
        ColumnAttr('notes', 'source.notes', type=str, width=20),
#        ColumnAttr('subgroups', 'source.subgroups', width=20),
    ]
    password = None

    def iterload(self):
        self.kp = read_kp(self.source, self.password)
        self.rows = []

        if self.kp:
            for group in self.kp.groups:
                yield KeePassGroupSheet(source=group, tableName=str(group))


KeePassIndexSheet.addCommand(ENTER, 'dive-row', 'vd.push(vd.push(cursorRow))')
KeePassIndexSheet.addCommand('^N', 'kdbx-password', 'unlock_kp()')
KeePassGroupSheet.addCommand(ENTER, 'copy-password', 'copy_password(cursorRow.password)')

vd.filetype('kdbx', KeePassIndexSheet)
addGlobals(globals())
