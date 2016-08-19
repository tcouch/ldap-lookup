#!/usr/bin/env python

import ldap
import sys
import getpass
from .ldapConfig import ldapConfig


class Connection(object):
    def __init__(self):
        self.server = ldapConfig["server"]
        self.base = ldapConfig["base"]
        self.conn = self.connect()
        
    def connect(self):
        uid = input('Enter your userid: ')
        pw = getpass.getpass("Password for {}: ".format(uid))
        ou = uid[0:4]
        bind_user = "cn={0}, ou={1}, {2}".format(uid, ou, self.base)
        try:
            connection = ldap.initialize(self.server)
            try:
                connection.bind_s(bind_user, pw)
            except ldap.INVALID_CREDENTIALS:
                print("Your username or password is incorrect.")
                sys.exit()
        except ldap.LDAPError as e:
            print(e)
            sys.exit()
        print("Connection to ldap successful")
        return connection

