# dsp-appsec-zap-automation

A tool for automating authenticated ZAP scans, using webdriver for login scripts and ZAP contexts for maintaining the session.

## How to add a site for scanning

There are several steps to adding a site to the list for scanning. The most important is creating a login script using one of the templates found under logins/templates/. The scripts use python and webdriver to login to the target site, setting the appropriate cookies before returning. 

After the login script has been created and tested, the site's information needs to be added to logins/allsites.json and sites.json. The allsites.json is not used at runtime, so the sites.json can be trimmed to only contain those sites you would like to run at a given time. 

There are several variables that need to be set in a local test.env file. This includes the username and passwords for the sites that need to login, as well as the report directory local to the ZAP instance and the proxy address and port. 

## How to run scans

Once the sites.json file contains the sites you want to scan, and the test.env file has been populated with the correct values, there are a couple steps to take to be able to run the script locally. 
You will need to make sure the python environment you're using has installed the libraries from requirement.txt.
You will also need to install the latest chrome driver, https://sites.google.com/a/chromium.org/chromedriver/downloads, and OWASP ZAP, https://www.zaproxy.org/download/.
Once ZAP is up and running, the scans specified in sites.json can be run by running scan.py. When each scan has finished it will output an xml report to the tmp/ directory.

(This would probably be good in a container.)

## Using the Juice Shop example


