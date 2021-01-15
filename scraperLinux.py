import sys, csv, time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

email="tech@crossculturedenver.org"
password="ccc!1234"
outputFile="credits.txt"

if len(sys.argv)<=1:
    print("\nWeb scraper for Cross Culture Denver A/V team")
    print("\nFunction: scrapes PlanningCenter pages for CCLI song numbers")
    print("    uses song numbers to scrape CCLI pages for legal info")
    print("    login info is hardcoded in script")
    print("    prints output to screen and also $HOME/"+outputFile)
    print("      (on windows 10 $HOME is usually C:/Users/windows)")
    print("\nUsage: python scraper4.py <url> ")
    print("   If url is from planningcenter, it will scrape the page for all songs")
    print("   If url is from songselect, it will scrape that page for the one song")
    print("    (this is intended to be used manually in case the song number isnt found)")
    print("\n   Examples: ")
    print("     python scraper4.py https://services.planningcenteronline.com/plans/1234567 ")
    print("     python scraper4.py https://songselect.ccli.com/Songs/7104200 ")
    print("\ncrossculturedenver.org")
    sys.exit()

### do it with firefox
###firefoxProfile = webdriver.FirefoxProfile(r'C:\Users\windows\AppData\Roaming\Mozilla\Firefox\Profiles\2ieb5mqz.default-release')
firefoxProfile = webdriver.FirefoxProfile('/home/echo/.mozilla/firefox//146ft793.default-release')
browser = webdriver.Firefox(firefox_profile=firefoxProfile,executable_path='/usr/bin/geckodriver')

### to do it with chrome, uncomment these lines and comment the above (firefox) lines
#opts = webdriver.ChromeOptions() 
#opts.add_argument("user-data-dir=C:\\Users\\windows\\AppData\\Local\\Google\\Chrome\\User Data")
#browser=webdriver.Chrome(options=opts)

#write text to an output file. if False, print to screen only
writeFile=True
footerText="All songs used by permission. CCLI#: 11413290"
maxCopyrightLineSize=50

debug=False

class CCLI_scraper():
    def __init__(self,argument):
      myUrl=argument[0]
      if "songselect.ccli.com" in myUrl:
        self.scrapeOne(myUrl)
      elif "services.planningcenteronline.com" in myUrl:
        self.scrapeAll(myUrl)

    def scrapeOne(self,page):
      allLines=[]
      failed=[]
      lines=self.scrapePage(page)
      allLines.extend(lines)
      browser.close()
      allLines.append("")
      allLines.append(footerText)
      print("")
      print(footerText)
      if writeFile: self.writeToTextFile(allLines)
      for f in failed:
        error="\n===============FAILED to find info for song: "+f
        print(error)
        #if writeFile: self.writeToTextFile(error)

    def scrapeAll(self,page):
        allLines=[]
        failed=[]
        songs=self.getCCLIpages(page)
        for song in songs:
          try:
            lines=self.scrapePage(song)
            allLines.extend(lines)
          except:
            failed.append(song)
        browser.close()
        allLines.append("")
        allLines.append(footerText)
        print("")
        print(footerText)
        if writeFile: self.writeToTextFile(allLines)
        for f in failed:
            error="\n===============FAILED to find info for song: "+f
            print(error)
            #if writeFile: self.writeToTextFile(error)

    def getCCLIpages(self,page):
        resultPages=[]
        browser.get(page)
        objSongLinks=browser.find_elements_by_xpath('//a[@class="control arrangement icon arrangement"]')
        allSongLinks=[x.get_attribute('href') for x in objSongLinks]
        for songLink in allSongLinks:
          browser.get(songLink)
          ccliNumber=browser.find_element_by_xpath('//div[@class="t-2 white mb-0.5"]')
          labelAndNum=ccliNumber.text.split("|")[0]
          print("Found:",labelAndNum)
          if "#" not in labelAndNum:
            print("\n===============FAILED to find CCLI number for song: "+songLink)
          else:
            numOnly=labelAndNum.split("#")[1]
            scrapeUrl="https://songselect.ccli.com/Songs/"+numOnly
            resultPages.append(scrapeUrl)
            if debug: print(scrapeUrl)
            #from selenium.webdriver.common.action_chains import ActionChains
            #action = ActionChains(browser)
            #action.move_to_element(songLink).perform()
            #songLink.click()
            #browser.execute_script("window.history.go(-1)")
        return resultPages

    def clickSignIn(self):
        try:
          signInLink = browser.find_element_by_class_name('color-e')
          if signInLink and signInLink.text=="Sign In":
            if debug: print("Found sign in link:",signInLink.text)
            signInLink.click()
            emailField = browser.find_element_by_id('EmailAddress')
            emailField.send_keys(email)
            passwordField = browser.find_element_by_id('Password')
            passwordField.send_keys(password)
            signinButton = browser.find_element_by_id('sign-in')
            signinButton.click()
            time.sleep(1)
            return True
        except NoSuchElementException:
          if debug: print("No sign in link found, attempting to get text...")
        return False

    def scrapePage(self,page):
        browser.get(page)
        if(self.clickSignIn()): print("logged in.")
        #browser.get(page) #re-get the page
        
        name=self.getSongName(browser)
        authors=self.getAuthors(browser)
        
        copyrights=[]
        administrators=[]
        metaLists = browser.find_element_by_class_name('song-meta')
        dataLists = metaLists.find_elements_by_tag_name('ul')
        for each in dataLists:
            listItems = each.find_elements_by_tag_name('li')
            title,elements=self.getFormattedList(listItems)
            if title=="Copyrights":
                copyrights.extend(elements)
            #if title=="Administrators":
            #    administrators.extend(elements)
        
        cdate,copyrights=self.moveCopyrightDate(copyrights)
        if cdate==None:
            cdate=" "
        #administrators=self.cleanupAdministrators(administrators)
        
        fileLines=[]
        nameHeader=name.upper()
        fileLines.append("")
        fileLines.append(nameHeader)
        arrHeader="Arrangement:"
        cHeader="Copyrights: © "+cdate
        adminHeader="Administrators:"
        fileLines.append(arrHeader)
        for each in authors:
            fileLines.append("   "+each)
        fileLines.append(cHeader)
        for each in copyrights:
          if(len(each)>maxCopyrightLineSize):
            splitLine=each.split("(")
            fileLines.append("   "+splitLine[0])
            for i in range(1,len(splitLine)):
              fileLines.append("      "+splitLine[i])
          else:
            fileLines.append("   "+each)
        #fileLines.append(adminHeader)
        #for each in administrators:
        #    fileLines.append("   "+each)

        for each in fileLines:
          print(each)
        return fileLines

    def writeToTextFile(self,lines):
        with open(outputFile, 'w') as writer:
          for each in lines:
            writer.write(each+"\n")
        writer.close()

    def getSongName(self,browser):
        title = browser.find_element_by_class_name('content-title') 
        nameString = title.find_elements_by_tag_name('h1')
        return nameString[0].text

    def getAuthors(self,browser):
        authors=[]
        title = browser.find_element_by_class_name('content-title') 
        dataList = title.find_elements_by_tag_name('li') 
        for item in dataList: 
            text = item.text 
            authors.append(text)
        return authors
        
    def getFormattedList(self,mylist):
        first=False
        title=""
        elements=[]
        for entry in mylist:
            each=entry.text
            if not first:
                title=each
                first=True
            else:
                elements.append(each)
        return title,elements
    
    def moveCopyrightDate(self,myList):
        myDate=None
        first=myList[0].split()
        if first[0].isdigit():
            myDate=first[0]
            replacement=" ".join(first[1:])
            myList[0]=replacement
        return myDate,myList
    
    def cleanupAdministrators(self,myList):
        if len(myList)==1 and ", " in str(myList[0]):
            myList=myList[0].split(", ")
        return myList


pages=sys.argv[1:]
myScraper=CCLI_scraper(pages)
