#!/usr/bin/env python

import ldap
import sys
import getpass
import csv
import re
import ldapConfig
import pickle


def getSearchTermType(searchTerm):
        if isEmail(searchTerm):
                searchTermType = "Email"
        elif isUPI(searchTerm):
                searchTermType = "UPI"
        elif isUsername(searchTerm):
                searchTermType = "Username"
        else:
                print("Searching for Full Name...")
                searchTermType = "Full Name"
        return searchTermType

def isUsername(searchTerm):
        if re.match(r'^[a-z0-9]{7}$',searchTerm):
                print ("Searching for Username...")
                return True
        else:
                return False
        
def isEmail(searchTerm):
        if re.match(r'.+@.+',searchTerm):
                print ("Searching for Email...")
                return True
        else:
                return False

def isUPI(searchTerm):
        if re.match(r'^[a-z]{5}[0-9]{2}$',searchTerm):
                print ("Searching for UPI...")
                return True
        else:
                return False

def chooseResult(ldapEntry):
        count = 1
        choices = []
        for x in ldapEntry:
                dept = ''.join(x[-1].get('department','Not found'))
                sn = ''.join(x[-1].get('sn','Not found'))
                gn = ''.join(x[-1].get('givenName','Not found'))
                mail = ''.join(x[-1].get('mail','Not found'))
                choices.append([count, gn, sn, mail, dept])
                count += 1
        print("\nPlease select which of these is most likely to be the person you are looking for:")
        print("")
        for i in choices:
                print ("%d:\t%s\t%s\t%s\t%s") % (i[0],i[1],i[2],i[3],i[4])
        validSelection = False
        while validSelection == False:
                selection = input("\nEnter a number from the choices above: ")
                try:
                        selection = int(selection)
                        if selection > 0 and selection < count:
                                validSelection = True
                        else:
                                print ("Please enter a number from 1 to %d") % (count - 1)
                except:
                        print ("Please enter a number from 1 to %d") % (count - 1)
        return ldapEntry[int(selection)-1][1]
                 
def getInput():
        qString = "Would you like to import search items from a file(f/F)" \
                  " or enter manually(m/M)?"
        inputMethod = input(qString)
        if inputMethod in ["f","F"]:
                searchList = getInputFromFile()
        elif inputMethod in ["m","M"]:
                searchList = getManualInput()
        else:
                print("You did not enter a valid response")
                con.unbind()
                sys.exit()
        return searchList

def getInputFromFile():
        searchList = []
        fileFound = False
        while fileFound == False:
                qString = "Please type the name of the file:"
                fileName = input(qString)
                try:
                        with open(fileName, 'rb') as inputFile:
                                reader = csv.reader(inputFile, delimiter=',')
                                for row in reader:
                                        searchList.append(row[0])
                        fileFound = True
                except IOError:
                        print("Could not locate that file.")
        return searchList

def getManualInput():
        qString = "Enter one or more emails, names, usernames or UPIs " \
                  "separated by commas:"
        searchInputString = input(qString)
        searchList = searchInputString.split(",")
        return searchList
        
def saveToFile(resultsList):
        qString = "Please type a file name for the output:"
        fname = input(qString)
        if fname == "":
                sys.exit()
        outputKeys = ['Search Term',
                      'Title',
                      'First Name',
                      'Last Name',
                      'Username',
                      'UPI',
                      'Email',
                      'Telephone',
                      'Department',
                      'Faculty',
                      'Full Name']
        writer = csv.DictWriter(open(fname, 'wb'), outputKeys, restval="Not Found")
        writer.writeheader()
        writer.writerows(resultsList)

def setupLDAPConnection():
        user_name = None
        pw = None
        
        usage="""%s [username]

        If a username is specified, this will be used as the SASL ID. 
        Otherwise,the user will be prompted for a username for ldap
        authentication.""" % sys.argv[0]

        if len(sys.argv) > 1:
                if sys.argv[1] == "-h" or sys.argv[1] == "--help":
                        print(usage)
                        sys.exit()
                else:
                        user_name = sys.argv[1]
        else:
                user_name = input('Enter your UCL username: ')

        pw = getpass.getpass("Password for %s: " % user_name)
        
        server = ldapConfig.ldapConfig["server"]
        ou = user_name[0:4]
        bind_user = "cn=%s,ou=%s,ou=Departments,dc=uclusers,dc=ucl,dc=ac,dc=uk" % (user_name, ou)

        try:    
                con = ldap.initialize(server)
                try:
                        con.bind_s(bind_user, pw)
                except ldap.INVALID_CREDENTIALS:
                        print("Your username or password is incorrect.")
                        sys.exit()
        except ldap.LDAPError as e:
                if type(e.message) == dict and e.message.has_key('desc'):
                        print(e.message['desc'])
                else:
                        print(e)
                sys.exit()
        print("Connection to ldap successful")
        return con

def getResults(con,searchList):
        with open('ldaphistory.pkl','rb') as ldapHistoryFile:
                ldapHistory = pickle.load(ldapHistoryFile)
        resultList = []
        for searchTerm in searchList:
                searchTerm = searchTerm.lower()
                searchTermType = getSearchTermType(searchTerm)
                searchResult = [ldapData for ldapData in ldapHistory if ldapData[searchTermType] == searchTerm]
                if not searchResult:
                        searchResult = queryLDAP(con,searchTerm,searchTermType)
                        if searchResult["Username"] != "Not found":
                                ldapHistory.append(searchResult)
                                with open('ldaphistory.pkl','wb') as ldapHistoryFile:
                                        pickle.dump(ldapHistory,ldapHistoryFile)
                resultList.append(searchResult)
        return resultList

def queryLDAP(con,searchTerm,searchTermType):
        searchResult = {}
        base= "ou=Departments,dc=uclusers,dc=ucl,dc=ac,dc=uk"
        fields = ["title",'department','sn','givenName',
                  'mail','telephoneNumber','employeeID','cn']
        if searchTermType == "Email":
                filterString = "(proxyAddresses=*%s*)" % (searchTerm)
        else:
                filterString = "(anr=%s)" % (searchTerm)
        ldapEntry = con.search_s(base,
                                    ldap.SCOPE_SUBTREE,
                                    filterString,
                                    fields
                                    )
        if len(ldapEntry) > 1:
                ldapEntry = chooseResult(ldapEntry)
        elif len(ldapEntry) == 0:
                ldapEntry = {}
        else:
                ldapEntry = ldapEntry[0][1]
        print(ldapEntry)
        searchResult["Title"] = str(ldapEntry.get('title','Not found')[0], 
                                    encoding='UTF-8')
        searchResult["Department"] = str(ldapEntry.get('department','Not found')[0],
                                         encoding='UTF-8')
        searchResult["Last Name"] = str(ldapEntry.get('sn','Not found')[0], 
                                        encoding='UTF-8')
        searchResult["First Name"] = str(ldapEntry.get('givenName','Not found')[0],
                                         encoding='UTF-8')
        searchResult["Email"] = str(ldapEntry.get('mail','Not found')[0], 
                                    encoding='UTF-8')
        searchResult["Telephone"] = str(ldapEntry.get('telephoneNumber','Not found')[0],
                                        encoding='UTF-8')
        searchResult["UPI"] = str(ldapEntry.get('employeeID','Not found')[0], 
                                  encoding='UTF-8')
        searchResult["Username"] = str(ldapEntry.get('cn','Not found')[0], 
                                       encoding='UTF-8')
        searchResult["Full Name"] = searchResult["First Name"] + " " + searchResult["Last Name"]
        searchResult["Search Term"] = searchTerm
        searchResult["Faculty"] = getFaculty(searchResult["Department"])
        return searchResult

def displayOutput(searchList,results):
        count = 0
        for result in results:
                print("Search Term %s found:") % (searchList[count])
                count += 1
                print(result["Title"], " ", result["First Name"], " ", result["Last Name"])
                print("Email: %s") % (result["Email"])
                print("Telephone: %s") % (result["Telephone"])
                print("UPI: %s") % (result["UPI"])
                print("Username: %s") % (result["Username"])
                print("Department: %s") % (result["Department"])
                print("Faculty: %s") % (result["Faculty"])
                print("\n")
        return 0

def getFaculty(dept):
        #lookup faculty in orgchart file using department
        orgchart = "orgchart.csv"
        with open(orgchart, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if dept == row[1]:
                    return row[7]
        return "Faculty not found"
                
def savedCopyWanted():
        query = "Would you like to save a copy? (y/n)"
        response = input(query)
        if response in ["Y","y"]:
                return True
        elif response in ["N","n"]:
                return False
        else:
                sys.exit()
                


def main():
        con = setupLDAPConnection()
        searchList = getInput()
        results = getResults(con,searchList)
        displayOutput(searchList,results)
        if savedCopyWanted():
                saveToFile(results)
  
if __name__ == "__main__":
  main()
