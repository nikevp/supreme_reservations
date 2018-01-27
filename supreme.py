import json
import time
import requests
import threading
import datetime
from requests import Session
from profiles import profiles_list
from bs4 import BeautifulSoup as bs



'''
1)Detect when page goes live
2)get captcha/harvest
3)get auth token from page
4)post first page
5)post second page with gcap
'''

#**********************************************************************#
baseURL = 'https://register.supremenewyork.com/'
postURL = 'https://register.supremenewyork.com/customers'
supKey = '6LfEPy8UAAAAAAVCidikQMCi4wIm_D-UMWSSJKHq'
captchaNumb = 2
#**********************************************************************#
apikey2captcha = ''
#**********************************************************************#
#  Captcha
#**********************************************************************#

def d_(destroyerId=None):
  if destroyerId is not None:
    return "Destroyer # "+str(destroyerId).rjust(4," ")+" "+str(datetime.datetime.now().time().strftime("%I:%M:%S.%f")[:-3])
  else:
    return "Destroyer # BASE "+str(datetime.datetime.now().time().strftime("%I:%M:%S.%f")[:-3])

class MyCaptchaThreads(threading.Thread):
    """
    Threading wrapper to handle counting and processing of tasks
    """
    def __init__(self, captchaURL, sitekey, apikey2captcha):
        self.captchaURL = captchaURL
        self.sitekey = sitekey
        self.apikey2captcha = apikey2captcha
        self.session = Session()
        threading.Thread.__init__(self)

    def run(self):
        """TASK RUN BY THREADING"""
        global captcha_list
        while True:
            self.validToken = self.getACaptchaToken()
            self.appendCaptcha()

    def getACaptchaToken(self):
        apikey2captcha = self.apikey2captcha
        sitekey = self.sitekey
        pageurl= self.captchaURL
        sleeping = 2
        session=requests.Session()
        session.verify=False
        session.cookies.clear()
        while True:
            data={
                "key":apikey2captcha,
                "action":"getbalance",
                "json":1,
                }
            response=session.get(url="http://2captcha.com/res.php",params=data)
            JSON=json.loads(response.text)
            if JSON["status"] == 1:
                balance=JSON["request"]
                print (d_()+ "Balance" + "$"+str(balance))
            else:
                print (d_()+ "Balance")
            CAPTCHAID=None
            proceed=False
            while not proceed:
                data={
                "key":apikey2captcha,
                "method":"userrecaptcha",
                "googlekey":sitekey,
                "pageurl":pageurl,
                "json":1
                }
                response=session.post(url="http://2captcha.com/in.php",data=data)
                JSON=json.loads(response.text)
                if JSON["status"] == 1:
                    CAPTCHAID=JSON["request"]
                    proceed=True
                else:
                    print (d_()+ "Response" + response.text)
                    print (d_()+ "Sleeping"+ str(sleeping)+" seconds")
                    time.sleep(sleeping)
            print (d_()+ "Waiting" +str(sleeping)+" seconds before polling for Captcha response")
            time.sleep(sleeping)
            TOKEN=None
            proceed=False
            while not proceed:
                data={
                "key":apikey2captcha,
                "action":"get",
                "json":1,
                "id":CAPTCHAID,
                }
                response=session.get(url="http://2captcha.com/res.php",params=data)
                JSON=json.loads(response.text)
                if JSON["status"] == 1:
                    TOKEN=JSON["request"]
                    proceed=True
                    print (d_()+ "Token ID" + TOKEN)
                else:
                    time.sleep(sleeping)
            data={
            "key":apikey2captcha,
            "action":"getbalance",
            "json":1,
            }
            response=session.get(url="http://2captcha.com/res.php",params=data)
            JSON=json.loads(response.text)
            if JSON["status"] == 1:
                balance=JSON["request"]
                print (d_()+ "Balance"+ "$"+str(balance))
            else:
                print (d_() + "Balance")
            if TOKEN is not None:
                return TOKEN

    def appendCaptcha(self):
        list = captcha_list
        with thread_lock:
            #print ('appending ' + str(list))
            list.append(self.validToken)
        time.sleep(50)
        if self.validToken in list:
            print ('sleeping longer')
            time.sleep(50)
            with thread_lock:
                try:
                    list.remove(self.validToken)
                except:
                    pass #already used
        else:
            print('token was used before expiring')
            return

def startCaptchaThreads(checkout_URL, sitekey, captchaNumb, apikey2captcha):
    for x in range(captchaNumb): # the number determines the # of captcha threads
        t=MyCaptchaThreads(checkout_URL, sitekey, apikey2captcha)
        t.daemon=True # allows us to send an interrupt
        threads.append(t)
        t.start()
        ## start the threads

threads = []
thread_lock = threading.Lock()
captcha_list = []


def rapidFireSlots(baseURL, postURL):
    for x in profiles_list:
        response = requests.get(baseURL)
        soup = bs(response.text, 'html.parser')
        post(postURL, getCSRF(soup), getCaptchaToken(), x)

def post(postURL, auth_token, g_token, contact_dict):
    headers = {'Content-Type': 'application/x-www-form-urlencoded','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','Accept-Language': 'en-US,en;q=0.8','User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'}
    params = {'authenticity_token': auth_token,
    'customer[name]': contact_dict['name'],
    'customer[email]':contact_dict['email'],
    'customer[tel]':contact_dict['tel'],
    'customer[location_preference]':contact_dict['location'],
    'customer[street]':contact_dict['addy'],
    'customer[street_2]':'',
    'customer[zip]':contact_dict['zip'],
    'customer[city]':contact_dict['city'],
    'customer[state]':contact_dict['state'],
    'credit_card[cn]':contact_dict['card_number'],
    'credit_card[month]':contact_dict['card_month'],
    'credit_card[year]':contact_dict['card_year'],
    'credit_card[verification_value]':contact_dict['card_cvv'],
    'g-recaptcha-response': g_token }

    response = requests.post(postURL, params=params, headers=headers)
    print (response.url, response.status_code)

def getCaptchaToken():
    global captcha_list
    empty = True
    while empty == True:
        if not captcha_list:
            time.sleep(.2)
            print('waiting')
        else:
            try:
                G = captcha_list.pop()
                #empty = False
                return G
            except:
                time.sleep(.2)
                print('likely thread deleted at the same time, reattempting')

def getCSRF(soup):
    script = soup.find('meta', {'name':'csrf-token'})
    formKey = script.get('content')
    return formKey



def main(baseURL, postURL):
    monitor = True
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36"}
    while monitor == True:
        response = requests.get(baseURL, headers=headers)
        soup = bs(response.text, 'html.parser')
        form = soup.find('form', {'id': 'signup_form'})
        if form:
            print('Reservations arent open')
        else:
            print('Reservations open. Reserving spots.')
            rapidFireSlots(baseURL, postURL)
            monitor = False
        time.sleep(1) #instead of time you can add proxy support

startCaptchaThreads(postURL, supKey, captchaNumb, apikey2captcha)
main(baseURL, postURL)

'''
Getting ready for Reservations
1) set contact_dict(s)
2) verify url
3) set captcha #
4)start 2 mins before

'''







#
