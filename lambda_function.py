
"""
Copyright (C) Quantum Dots - All Rights Reserved
Unauthorized distribution of this file, via any medium is strictly prohibited
Proprietary and confidential
You may modify the code only for personal purposes
Written by Abel C Dixon <abelcheruvathoor@gmail.com>, October 2021
"""

from __future__ import print_function

import math
import os

### IF USING CONFIGURATIONS.PY FILE ###

'''
KITE_USERNAME = configurations.KITE_USERNAME
KITE_PASSWORD = configurations.KITE_PASSWORD
CDSL_PIN = configurations.CDSL_PIN
KITE_SECRET = configurations.KITE_SECRET
'''

### END OF CONFIGURATIONS.PY FILE ###


### IF USING ENVIRONMENT VARIABLES FROM AWS LAMBDA ###

# Uncomment the following lines if using environment variables from AWS Lambda


KITE_USERNAME = os.environ.get('KITE_USERNAME')
KITE_PASSWORD = os.environ.get('KITE_PASSWORD')
CDSL_PIN = os.environ.get('CDSL_PIN')
KITE_SECRET = os.environ.get('KITE_SECRET')


### END OF ENVIRONMENT VARIABLES ###

# 6 digit OTP regular expression
pattern = '(\d{2}):(\d{2}):(\d{2})'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

try:
    import json
    from selenium.webdriver import Chrome
    from selenium.webdriver.chrome.options import Options
    import shutil
    import uuid
    import boto3
    from datetime import datetime
    from dateutil.tz import gettz
    import time

    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    import re

    import base64
    import hmac
    import secrets
    import struct
    import sys


    print("All Modules Imported")

    global msg
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

except Exception as e:
    print(e)

new_email_second = -math.inf
new_email_hour = 0
new_email_date = datetime.fromisoformat('2021-10-22 10:46:37+05:30')


class WebDriver(object):

    def __init__(self):
        self.options = Options()

        self.options.binary_location = '/opt/headless-chromium'
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--start-maximized')
        self.options.add_argument('--start-fullscreen')
        self.options.add_argument('--single-process')
        self.options.add_argument('--disable-dev-shm-usage')

    def get(self):
        driver = Chrome('/opt/chromedriver', options=self.options)
        return driver



def hotp(key, counter, digits=6, digest='sha1'):
    key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    counter = struct.pack('>Q', counter)
    mac = hmac.new(key, counter, digest).digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack('>L', mac[offset:offset+4])[0] & 0x7fffffff
    return str(binary)[-digits:].zfill(digits)


def totp(key, time_step=30, digits=6, digest='sha1'):
    return hotp(key, int(time.time() / time_step), digits, digest)


def lambda_handler(event, context):
    OTP = 0
    global new_email_second, new_email_hour, new_email_date

    instance_ = WebDriver()
    driver = instance_.get()

    current_time = datetime.now(tz=gettz('Asia/Kolkata'))

    KITE_URL = "https://kite.zerodha.com/"
    HOLDINGS_URL = "https://kite.zerodha.com/holdings"

    driver.get(KITE_URL)

    #  filling the user id and password
    driver.find_element_by_id('userid').send_keys(KITE_USERNAME)
    driver.find_element_by_id('password').send_keys(KITE_PASSWORD)

    driver.find_element_by_class_name("button-orange").click()
    driver.implicitly_wait(60)

    # entering security pin
    totp_val = totp(KITE_SECRET)
    print(f"TOTP : {totp_val}")
    driver.find_element_by_xpath("//input[@type='text']").send_keys(totp_val)
    #  driver.find_element_by_class_name("button-orange").click()  ; No more required
    driver.implicitly_wait(60)
    time.sleep(2)

    # navigating to holding page
    driver.get(HOLDINGS_URL)
    driver.implicitly_wait(60)
    time.sleep(2)

    # selecting "Authorisation" option
    driver.find_element_by_xpath("//a[text()='Authorisation']").click()
    time.sleep(2)
    driver.implicitly_wait(60)
    kite_window = driver.window_handles[0]

    # Selecting "Continue" in authorisation pop up
    driver.find_element_by_xpath("//button[text()='Continue ']").click()

    time.sleep(2)
    driver.implicitly_wait(60)

    # Switching to CDSL page
    cdsl_window = driver.window_handles[1]
    driver.switch_to.window(cdsl_window)
    driver.implicitly_wait(120)
    time.sleep(4)

    driver.find_element_by_xpath("/html/body/div[1]/div/div/div[2]/div[2]/button").click()

    time.sleep(3)

    # Entering TPIN
    driver.find_element_by_id("txtPIN").send_keys(CDSL_PIN)
    driver.find_element_by_id("btnCommit").click()
    driver.implicitly_wait(60)

    print(f"Current time : {current_time}")

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API and check for latest email from cdsl
    # Analysing the time of arrival of email
    while new_email_date < current_time:

        results = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX'],
                                                  q="from:edis@cdslindia.co.in is:unread").execute()
        message = results.get('messages', [])[0]

        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        email_data = msg['payload']['headers']

        for values in email_data:
            name = values["name"]
            if name == "Date":
                date = values["value"]

                try:
                    # if date is like Tue, 29 Mar 2022 09:04:37 +0530
                    new_email_date = str(date[:-12])
                    new_email_date += '+05:30'

                    new_email_date = datetime.strptime(new_email_date, "%a, %d %b %Y %H:%M:%S%z")
                except:
                    # if date is like 29 Mar 2022 09:04:37 +0530
                    new_email_date = str(date[:-6])
                    new_email_date += '+05:30'

                    new_email_date = datetime.strptime(new_email_date, '%d %b %Y %H:%M:%S%z')


    print(f"New Email : {new_email_date}")
    results = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX'],
                                              q="from:edis@cdslindia.co.in is:unread").execute()
    message = results.get('messages', [])[0]

    # for message in messages:
    msg = service.users().messages().get(userId='me', id=message['id']).execute()

    email_data = msg['payload']['headers']

    for values in email_data:
        name = values["name"]
        if name == "Date":
            date = values["value"]
            match = re.search(pattern, str(date))
            new_email_hour = int(match.group()[0:2])
            new_email_second = (int(match.group()[3:5]) * 60) + int(match.group()[6:9])

    matchOTP = re.search('(\d{6})', str(msg['snippet']))
    OTP = matchOTP.group()

    print(f"OTP = {OTP}")

    driver.implicitly_wait(60)
    driver.switch_to.window(cdsl_window)
    driver.implicitly_wait(60)
    driver.find_element_by_id("OTP").send_keys(OTP)
    driver.implicitly_wait(60)
    driver.find_element_by_id("VerifyOTP").click()
    driver.implicitly_wait(60)
    print("Success")
    driver.quit()

    print("Done")

    return True
