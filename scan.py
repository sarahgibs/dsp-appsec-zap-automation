from http.client import PROXY_AUTHENTICATION_REQUIRED
import json
import time
import os
import logging

from zapv2 import ZAPv2
import importlib

from dotenv import load_dotenv

load_dotenv()


def new_context(zap, domain):
    """
    Creates a new context in zap for the particular scan.
    """
    zap.context.new_context(domain)
    #context name, regex of included sites
    zap.context.include_in_context(domain, ".*"+domain+".*")
    zap.authentication.set_authentication_method(2,"manualAuthentication")
    #returning context name. In case this code changes.
    return domain
    

def cookieauth(zap,contextID,context):
    """
    Sets up the ZAP context to use cookies for authentication.
    Only works if the cookie used by the app is recognized as a session cookie by ZAP.
    """
    username = "testuser"
    zap.users.new_user(contextID, username)
    userid = zap.users.users_list(contextID)[0]["id"]
    #this is the secret sauce for using cookies. The user above is now associated with the active cookie.
    #It should always choose the newest one.
    sessions=zap.httpsessions.sessions(site = context)
    sessionName=sessions[-1]["session"][0]
    zap.users.set_authentication_credentials(contextID,userid,"sessionName=" + sessionName)

    zap.users.set_user_enabled(contextID,userid,True)
    zap.forcedUser.set_forced_user(contextID,userid)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    return username, userid

def tokenauth(zap, contextID, domain):
    """
    Sets up the ZAP context to use tokens for authentication.
    Only works if the token has been put in the sessid cookie.
    """
    username = "testuser"
    zap.users.new_user(contextID, username)
    userid = zap.users.users_list(contextID)[0]["id"]

    #ZAP needs the port, if testing locally over a different port, update this value.
    sessions = zap.httpsessions.sessions(site = domain)

    #sessid is identified by ZAP as a session cookie by default. 
    #It probably makes sense to have the cookie used be controlled by config.
    try:
        token = sessions[-1]["session"][1]["sessid"]["value"]
    except:
        logging.info("Failed to find cookie with token")
        
    #the token auth script is general purpose, as long as the sessid cookie is used for storing the token.
    #This works when ZAP is local.
    cwd = os.getcwd()
    scriptlocation = cwd + "/scripts/token_auth.js"
    scriptname = "token_auth.js"
    zap.script.load(scriptname,"httpsender","ECMAScript : Oracle Nashorn",scriptlocation)


    zap.script.set_global_var("token",token)

    zap.users.set_user_enabled(contextID,userid,True)
    zap.forcedUser.set_forced_user(contextID,userid)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    zap.script.enable(scriptname)
    return username, userid, scriptname


def pullReport(zap, context, url, site):
    """
    Requests report from ZAP and saves it in the directory specified.
    Directory must be local to ZAP.
    """
    template = "traditional-xml"
    zap.reports.generate(title=site, template=template, contexts=context, sites=url, reportdir=os.getenv("REPORT_DIR"))


def loginAndScan(proxy, site, env):
    """
    Calls the login function for the site being scanned, 
    and then runs crawlers and scans against it.
    """
    module = importlib.import_module("logins." + site)
    login = getattr(module, "login")
    
    domain, authtype, logged_in=login(proxy,env)
    if logged_in == False:
        logging.info("Failed to login, no scan will be performed.")
        return

    #all sites will need to connect to zap and create a context.
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    context = new_context(zap, domain)
    contextID = zap.context.context(context)["id"]

    #There's probably a way to make this better. probably by putting it in the login script
    zap.context.exclude_from_context(context, ".*/login.*")
    zap.context.exclude_from_context(context, ".*/logout.*")
    zap.context.exclude_from_context(context, ".*/complete.*")

    if authtype == "cookie":
        userName, userId=cookieauth(zap, contextID, context)
    elif authtype == "token":
        userName, userId, scriptname=tokenauth(zap, contextID, domain)
   
    #passive scan
    zap.pscan.enable_all_scanners()
   
    #run spider
    zap.spider.scan_as_user(contextID, userId, "https://"+domain)
    time.sleep(5)
    while (zap.spider.status == "running"):
        logging.debug("Spider still running")
        time.sleep(5)
    logging.info("Spider complete")

    #run ajax spider
    #this needs to be configurable.
    zap.ajaxSpider.set_option_max_duration(5)
    zap.ajaxSpider.scan_as_user(context, userName, "https://"+domain)
    time.sleep(5)
    while (zap.ajaxSpider.status == "running"):
        logging.debug("Ajax Spider still running")
        time.sleep(5)
    logging.info("Ajax Spider complete")

    #Run active scan as the authenticated user.
    #Set to 1 minute for demonstration purposes
    zap.ascan.set_option_max_scan_duration_in_mins(1)
    zap.ascan.scan_as_user(contextid=contextID, userid=userId)
    time.sleep(10)
    while (zap.ascan.status == "running"):
        logging.debug("Active scanner running")
        time.sleep(5)
    logging.info("Active scanner complete")
    pullReport(zap, context, "https://" + domain, site)

    if authtype == "token":
        zap.script.disable(scriptname)



if __name__ == "__main__":
    load_dotenv("scan.env")
    logging.basicConfig(level="INFO")

    proxy = str(os.getenv("PROXY")) + ":" + str(os.getenv("PORT"))
    logging.info(proxy)
    #attempt to wait to initialize zap
    #only really needed if the zap instance is remote.
    time.sleep(10)

    f = open("sites.json", "r")
    sites = json.load(f)
    for elem in sites:
        print(elem["site"])
        loginAndScan(proxy, elem["login"], elem["env"])

    print("test complete")
   
    
    