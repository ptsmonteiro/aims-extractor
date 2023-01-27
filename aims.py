from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

import time
from datetime import date, timedelta

import csv
import json
import csvlogs

BLOCK_DAYS = 30

USERNAME_INPUT_ID="Id"
PASSWORD_INPUT_ID="Pass"
LOGIN_BUTTON_ID="login_button"
LOGOUT_BUTTON_ID="logout_button"

LOGBOOK_PAGE_LINK_ID="btn_24"

CSV_DATE_FROM_INPUT_ID="cal1"
CSV_DATE_TO_INPUT_ID="cal2"
CSV_DOWNLOAD_BUTTON_ID="csv_export"

config = None
driver = None
action = None

def init():
    global config
    with open('config.json') as json_file:
        data = json.load(json_file)
        config = data['aims']

    global driver, action
    fp = webdriver.FirefoxProfile(config['firefox_profile_path'])
    driver = webdriver.Firefox(fp)
    action = ActionChains(driver)

    #login()
    #goto_pilot_logbook()
    
def quit():
    driver.quit()

def login():
    global driver, action, config

    driver.get(config['url'])
    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, PASSWORD_INPUT_ID)))

    username_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, USERNAME_INPUT_ID)))
    time.sleep(2)
    action.move_to_element(username_field).perform()
    username_field.send_keys(config['username'])

    password_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, PASSWORD_INPUT_ID)))
    time.sleep(2)
    action.move_to_element(password_field).perform()
    password_field.send_keys(config['password'])

    # Find the login button and click it
    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, LOGIN_BUTTON_ID)))
    time.sleep(2)
    action.move_to_element(element).click().perform()

    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, LOGOUT_BUTTON_ID)))

def goto_pilot_logbook():
    global driver, action

    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, LOGBOOK_PAGE_LINK_ID)))
    time.sleep(5)
    action.move_to_element(element).click().perform()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, CSV_DATE_FROM_INPUT_ID)))

def fetch_csv(from_date, to_date):
    print("Fetching CSV from %s to %s" % (from_date, to_date))

    global driver, action

    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, CSV_DATE_FROM_INPUT_ID)))
    element.execute_script("document.getElementById('%s').setAttribute('value', '%s')" % (CSV_DATE_FROM_INPUT_ID, from_date))

    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, CSV_DATE_TO_INPUT_ID)))
    element.execute_script("document.getElementById('%s').setAttribute('value', '%s')" % (CSV_DATE_TO_INPUT_ID, to_date))

    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, CSV_DOWNLOAD_BUTTON_ID)))
    action.move_to_element(element).click().perform()

    # TODO complete/test this 

    return 

def get_flight_block(from_date, to_date):
    print("Getting flight block from %s to %s" % (from_date, to_date))

    # Don't fetch in the future
    if (to_date > date.today()): to_date = date.today()
    fetch_csv(from_date, to_date)

    flights = csvlogs.get_incoming_fligts()
    return flights

def get_flights(from_date):
    print("Getting AIMS flights from %s" % (from_date))

    flights = []

    # get blocks of max BLOCK_DAYS days
    to_date = from_date + timedelta(days=BLOCK_DAYS)
    while (from_date < date.today()):
        block_flights = get_flight_block(from_date, to_date)

        for bf in block_flights:
            flights.append(bf)

        from_date = to_date + timedelta(days=1)
        to_date = from_date + timedelta(days=BLOCK_DAYS)

    return flights
