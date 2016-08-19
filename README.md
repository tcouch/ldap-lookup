# ldap-lookup
Script for finding people in ldap

# Python modules required
python-ldap

# Setup
You'll need to create a file called ldapConfig.py containing the ldap server details like so:

```
ldapConfig = {
    "server":"ldap://ldap-server.example.com:389/",
    "base":"ou=something,dc=dom,dc=dom,dc=dom"
    }
```
