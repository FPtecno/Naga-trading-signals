import time
import requests
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import os
# import sys

from keys import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NAGA_USERNAME, NAGA_PASSWORD

# Add d:/Proy/intra to the Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
##################################################

SYMBOLS = ["EUR/USD","AUD/JPY"]


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_trading_signals():
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    # options.add_argument("--ignore-certificate-errors")  
    # options.add_argument("--allow-running-insecure-content")
    # options.add_argument("--disable-web-security")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://nagamarkets.com/login")
        wait = WebDriverWait(driver, 10)
        
        # Login
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "user_name")))
        username_field.send_keys(NAGA_USERNAME)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(NAGA_PASSWORD)
        
        # Click the login button
        sign_in_button = driver.find_element(By.CSS_SELECTOR, "button[data-cy='login-btn']")
        sign_in_button.click()

        time.sleep(5)  # Give time for the page to load

        # # Debug: Print page title after login
        # print("Page Title After Login:", driver.title)

        # Check if login failed (for example, if the login page is still present)
        if "Login" in driver.title:
            print("Login failed! Check your credentials.")
            send_telegram_message("Login failed! Check your credentials.")
            driver.quit()
            return pd.DataFrame()  # Return an empty dataframe to prevent errors
        
        driver.get("https://nagamarkets.com/trading-central-signals")
        time.sleep(3)

        # # Debug: Print part of the page source to check if content is loading
        # print(driver.page_source[:1000])  # Print the first 1000 characters
        
        # Extract Trading Signals Titles
        titles = [elem.text.strip() for elem in driver.find_elements(By.CSS_SELECTOR, "div.trkd-news-body__title")]
    
    finally:
        driver.quit()
    
    return pd.DataFrame(titles, columns=["Title"])

def main():
    try:
        actual_data = pd.read_csv("actual_data.csv")
    except FileNotFoundError:
        actual_data = pd.DataFrame(columns=["Symbol", "Date", "Title"])
    
    while True:
        new_data = get_trading_signals()
        
        if not new_data.empty:
            # Convert titles to uppercase
            new_data["Title"] = new_data["Title"].str.upper()
            
            # Filter new entries that start with any of the symbols
            new_data["Symbol"] = new_data["Title"].apply(lambda title: next((symbol for symbol in SYMBOLS if title.startswith(symbol)), None))
            new_data = new_data.dropna(subset=["Symbol"])
            new_data["Date"] = datetime.now().strftime("%d-%m-%Y %H:%M")
            
            combined_data = pd.concat([actual_data, new_data], ignore_index=True)
            combined_data = combined_data.drop_duplicates(subset=["Title", "Date"], keep='last')
            
            # Identify new entries
            new_entries = combined_data[~combined_data[["Title", "Date"]].isin(actual_data[["Title", "Date"]]).all(axis=1)]
            
            if not new_entries.empty:
                new_entries = new_entries[["Symbol", "Date", "Title"]]
                
                # Save new entries to actual_data.csv and send notification
                actual_data = pd.concat([actual_data, new_entries], ignore_index=True)
                actual_data.to_csv("actual_data.csv", index=False)
                send_telegram_message("New trading post available!")
                print("New trading post detected and notification sent.")
            else:
                print("No new trading posts.")
        
        time.sleep(60)  # Wait for 1 minute

if __name__ == "__main__":
    main()

# To execute the code. D:\Proyectos\trading-signals>py send_notif.py

