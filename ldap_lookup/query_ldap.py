#!/usr/bin/env python3

import re
from .ldap_conn import Connection

class Query(object):
    def __init__(self, searchterm, connection=None, fields=[]):
        self.searchterm = searchterm
        self.connection = connection
        self.searchtype = self.get_search_term_type()
        self.filter = self.get_filter()
        # Search for these default fields is none specifically requested
        if not fields:
            self.fields = ['title', 'department', 'sn', 'givenName',
                  'mail', 'telephoneNumber', 'employeeID', 'cn']
        else: self.fields = fields
        # If a connection object hasn't been passed, make one
        if not connection:
            self.connection = Connection()
        

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
        if re.match(r'.+@.+', self.searchterm): return "email"
        # Is it a UPI?
        elif re.match(r'^[a-z]{5}[0-9]{2}$', self.searchterm): return "UPI"
        # Is it a userid?
        elif re.match(r'^[a-z0-9]{7}$', self.searchterm): return "userid"
        # If none of the above assume it's a name
        else: return "name"


    def get_result(self):
        # second argument '2' = ldap.SCOPE_SUBTREE (saves importing ldap here)
        ldap_output = self.connection.conn.search_s(self.connection.base, 2,
                                                    self.filter, self.fields)
        if len(ldap_output) > 1:
            result = self.select_result(ldap_output)
        elif len(ldap_output) == 0:
            result = {}
        else: result = ldap_output[0][1]
        result = self.clean_result(result)
        self.result = result
        return self.result


    def clean_result(self, result):
        # string data needs converting to UTF-8 from bytes
        # because ldap is returning bytes for some reason
        cleaned = { k: result[k][0].decode('UTF-8') for k in result.keys() }
        return cleaned


    def select_result(self, ldap_output):
        count = 1
        choices = []
        for choice in ldap_output:
            cc = self.clean_result(choice[-1])
            choices.append([count, cc['givenName'], cc['sn'],
                           cc['mail'], cc['department']])
            count += 1
        print("\nPlease select which of these is most likely to be the person"
              " you are looking for:\n")
        for choice in choices:
            print("{0}:\t{1}\t{2}\t{3}\t{4}".format(*choice))
        valid_selection = False
        while not valid_selection:
            item_number = input("\nEnter a number from the choices above: ")
            try:
                selection = ldap_output[int(item_number)-1][1]
                valid_selection = True
            except:
                print("Not a valid selection!")
        return selection


if __name__ == "__main__":
    from sys import argv
    print(Query(argv[1]).get_result())
    
