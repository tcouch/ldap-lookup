#!/usr/bin/env python3

import re
from ldap3 import Server, Connection, core, ALL
from getpass import getpass
import sys
from .ldapConfig import ldapConfig


class LDAPConnection():
    def __init__(self):
        self.server = Server(ldapConfig['server'], get_info=ALL)
        self.FQDN = ldapConfig["FQDN"]
        self.uid = ldapConfig.get("uid")
        if not self.uid:
            self.uid = input('Enter your userid: ')
        self.pw = ldapConfig.get("pw")
        if not self.pw:
            self.pw = getpass("Password for {}: ".format(self.uid))
        self.bind_user = "CN={0},{1}".format(self.uid, self.FQDN)
        self.connection = self.make_connection()

    def make_connection(self):
        try:
            c = Connection(self.server,
                           self.bind_user,
                           self.pw,
                           auto_bind=True)
        except core.exceptions.LDAPBindError:
                print("Your username or password is incorrect.")
                sys.exit()
        except core.exceptions.LDAPExceptionError as e:
            print(e)
            sys.exit()
        return c


class Query(object):
    def __init__(self, searchterm, connection=None, fields=[]):
        self.searchterm = searchterm
        self.conn = connection
        self.searchtype = self.get_search_term_type()
        self.base = ldapConfig["base"]
        self.filter = self.get_filter()
        # Search for these default fields is none specifically requested
        self.fields = ['title', 'department', 'sn', 'givenName',
                       'mail', 'telephoneNumber', 'employeeID', 'cn']
        if fields:
            self.fields.extend(fields)
        # If a connection object hasn't been passed, make one
        if not connection:
            self.conn = LDAPConnection().make_connection()

    def get_filter(self):
        """Search proxy addresses if looking for email, otherwise use anr
        which covers all other cases"""
        if self.searchtype == "email":
            filter = "(proxyAddresses=*{}*)".format(self.searchterm)
        else:
            filter = "(anr={})".format(self.searchterm)
        return filter

    def get_search_term_type(self):
        # Is it an email?
        if re.match(r'.+@.+', self.searchterm):
            return "email"
        # Is it a UPI?
        elif re.match(r'^[a-z]{5}[0-9]{2}$', self.searchterm):
            return "UPI"
        # Is it a userid?
        elif re.match(r'^[a-z0-9]{7}$', self.searchterm):
            return "userid"
        # If none of the above assume it's a name
        else:
            return "name"

    def get_result(self):
        self.conn.search(self.base, self.filter, attributes=self.fields)
        ldap_output = self.conn.entries
        if len(ldap_output) > 1:
            result = self.select_result(ldap_output)
        elif len(ldap_output) == 0:
            result = {}
        else:
            result = ldap_output[0].entry_attributes_as_dict
        self.result = result
        return self.result

    def select_result(self, ldap_output):
        count = 1
        choices = []
        for entry in ldap_output:
            choices.append([count, entry.givenName, entry.sn,
                           entry.mail, entry.department])
            count += 1
        print("\nPlease select which of these is most likely to be the person"
              " you are looking for:\n")
        for choice in choices:
            print("{0}:\t{1}\t{2}\t{3}\t{4}".format(*choice))
        valid_selection = False
        while not valid_selection:
            item_number = input("\nEnter a number from the choices above: ")
            try:
                selection = ldap_output[int(item_number)-1]
                valid_selection = True
            except:
                print("Not a valid selection!")
        return selection.entry_attributes_as_dict


if __name__ == "__main__":
    from sys import argv
    print(Query(argv[1]).get_result())
