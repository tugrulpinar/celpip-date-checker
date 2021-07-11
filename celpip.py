import time
import smtplib
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from email.message import EmailMessage
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import Select
from apscheduler.schedulers.blocking import BlockingScheduler
import os


def find_click(element_id):
    variable = browser.find_element_by_id(element_id)
    variable.click()


def find_xpath_click(full_x_path):
    variable = browser.find_element_by_xpath(full_x_path)
    variable.click()


def fill_out(element_id, data):
    variable = browser.find_element_by_id(element_id)
    variable.send_keys(data)


def drop_down_selection(element_id, selection):
    variable = browser.find_element_by_id(element_id)
    var = Select(variable)
    var.select_by_visible_text(selection)


def send_email(url, availability_info):
    msg = EmailMessage()
    recipients = [os.environ["e_user"], os.environ["e_client"]]
    msg["Subject"] = "Test Centre is available!"
    msg["From"] = [os.environ["e_user"]
    msg["Bcc"] = ",".join(recipients)
    msg.set_content(
        f"Hi,\n\nThere may be some seats available in:\n\n {availability_info} !\n\n Check out the link:\n{url}")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

            smtp.login([os.environ["e_user"], [os.environ["e_pwd"])
            smtp.send_message(msg)
            print("Email sent!")
    except Exception as e:
        print(str(e))
        print("Failed to send email")


def celpip_checker():
    url = "https://secure.celpip.ca/RegWebApp/#/registration/test-selection"

    global browser
    browser = webdriver.Chrome()
    browser.get(url)
    browser.implicitly_wait(20)

    find_xpath_click(
        "/html/body/div[2]/div[2]/div[3]/div[2]/div/div[2]/div/div/div[3]/p/button")
    find_click("testTypeImgG")
    find_xpath_click(
        "/html/body/div[2]/div[2]/div[3]/div[2]/div/div[3]/div/div[1]/div[2]/p[3]/a")
    find_xpath_click(
        "/html/body/div[2]/div[2]/div[3]/div[2]/div/div[5]/div/div[1]/div[3]/label/input")
    find_xpath_click(
        "/html/body/div[2]/div[2]/div[3]/div[2]/div/div[5]/div/div[2]/div[1]/label/input")
    find_click("celpip-test-type-selection-go-next-button")

    drop_down_selection("sitting-selection-select-country-select", "CANADA")
    drop_down_selection("sitting-selection-select-region-select", "Ontario")
    time.sleep(6)

    # DOWNLOAD THE HTML CONTENT OF THE PAGE
    page = BeautifulSoup(browser.page_source, "html.parser")
    browser.quit()

    # FIND ALL THE "LI" LIST ITEM TAGS
    containers = page.findAll("li", {"class": "list-group-item"})

    # ONLY KEEP THE FIRST TEN, BECAUSE THOSE WILL GIVE THE EARLIEST DATES
    early_dates = containers[:10]

    # EXTRACT THE DATE OUT OF THE STRONG TAG AS TEXT
    dates = [item.strong.text for item in early_dates]

    # EXTRACT THE TEST CENTERS OUT OF THE STRONG TAG AS TEXT
    test_center = [item.text.split('\n')[7] for item in early_dates]
    combined = list(zip(dates, test_center))

    # only_dates = [item.split("-")[0].strip() for item in dates]

    # CONVERT THE TEXT INTO A DATETIME OBJECT SO WE CAN COMPARE
    only_dates = [datetime.strptime(item.split(
        "-")[0].strip(), '%b %d, %Y') for item in dates]

    # SET A THRESHOLD DATE
    date_threshold = datetime.strptime("Jun 3, 2021", '%b %d, %Y')

    df_available_dates = []
    df_test_centers = []

    # available_dates = []

    # IF THE DATE IS SMALLER THAN JUNE 3, 2021, KEEP IT
    for idx, item in enumerate(only_dates):
        if item < date_threshold:
            df_available_dates.append(dates[idx])
            df_test_centers.append(test_center[idx])

    # IF THE LIST IS NOT EMPTY, THAT MEANS THERE ARE SOME DATES SMALLER THAN JUNE 3, 2021. IN THAT CASE SEND EMAIL
    if df_available_dates:
        df = pd.Series(df_test_centers, index=[df_available_dates])
        send_email(url, df)
    else:
        now = datetime.now()
        print("No available dates at", now)


def scheduler():
    sched = BlockingScheduler()
    sched.add_job(celpip_checker, 'interval', minutes=20)
    sched.start()


scheduler()
# celpip_checker()
