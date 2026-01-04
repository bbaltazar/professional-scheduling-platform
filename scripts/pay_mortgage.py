#!/usr/bin/env python3
"""
Automated Mortgage Payment Script
Automates the payment process on portal.hoaorganizers.com using Selenium

PREREQUISITE: Run inspect_mortgage_site.py first to generate mortgage_selectors.json
"""

import os
import sys
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def load_selectors():
    """Load element selectors from JSON file"""
    selectors_file = Path(__file__).parent / 'mortgage_selectors.json'
    
    if not selectors_file.exists():
        print("❌ ERROR: mortgage_selectors.json not found!")
        print("\n📋 You need to run the inspector first:")
        print("   python scripts/inspect_mortgage_site.py")
        print("\nThis will help you identify the correct element selectors.")
        sys.exit(1)
    
    with open(selectors_file, 'r') as f:
        return json.load(f)


def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    # Uncomment the next line to run headless (without opening browser window)
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


def get_by_type(selector_type):
    """Convert selector type string to Selenium By type"""
    type_map = {
        'id': By.ID,
        'name': By.NAME,
        'css': By.CSS_SELECTOR,
        'text': By.XPATH,  # Will construct XPATH for text matching
        'xpath': By.XPATH
    }
    return type_map.get(selector_type, By.ID)


def find_and_click(driver, selector_info, step_name, timeout=20):
    """Find element using selector info and click it"""
    selector_type = selector_info['type']
    selector_value = selector_info['value']
    
    print(f"🔍 Looking for: {step_name} (type={selector_type}, value={selector_value[:30]}...)")
    
    # Handle text-based selectors (button/link text)
    if selector_type == 'text':
        # Try exact text match first
        xpath = f"//*[text()='{selector_value}']"
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return element
        except:
            # Try contains for partial match
            xpath = f"//*[contains(text(), '{selector_value}')]"
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return element
    
    # Handle CSS selectors
    elif selector_type == 'css':
        # Add dot if it's a class and doesn't have it
        if not selector_value.startswith('.') and not selector_value.startswith('#'):
            selector_value = f'.{selector_value}'
        by_type = By.CSS_SELECTOR
    else:
        by_type = get_by_type(selector_type)
    
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by_type, selector_value))
    )
    element.click()
    return element


def find_and_send_keys(driver, selector_info, keys, step_name, timeout=20):
    """Find input element using selector info and send keys"""
    selector_type = selector_info['type']
    selector_value = selector_info['value']
    
    print(f"🔍 Looking for input: {step_name} (type={selector_type}, value={selector_value[:30]}...)")
    
    # Handle CSS selectors
    if selector_type == 'css':
        if not selector_value.startswith('.') and not selector_value.startswith('#'):
            selector_value = f'.{selector_value}'
        by_type = By.CSS_SELECTOR
    else:
        by_type = get_by_type(selector_type)
    
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by_type, selector_value))
    )
    element.clear()
    element.send_keys(keys)
    return element


def wait_and_click(driver, by, value, timeout=20):
    """Wait for element to be clickable and click it"""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()
    return element


def wait_and_send_keys(driver, by, value, keys, timeout=20):
    """Wait for element to be present and send keys"""
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    element.clear()
    element.send_keys(keys)
    return element


def pay_mortgage():
    """Main function to automate mortgage payment"""
    
    # Load selectors from JSON
    print("📂 Loading element selectors...")
    selectors = load_selectors()
    
    # Get credentials from environment variables
    email = os.getenv('MORTGAGE_EMAIL')
    password = os.getenv('MORTGAGE_PASSWORD')
    phone = os.getenv('MORTGAGE_PHONE')
    routing_number = os.getenv('MORTGAGE_ROUTING_NUMBER')
    account_number = os.getenv('MORTGAGE_ACCOUNT_NUMBER')
    
    # Validate environment variables
    required_vars = {
        'MORTGAGE_EMAIL': email,
        'MORTGAGE_PASSWORD': password,
        'MORTGAGE_PHONE': phone,
        'MORTGAGE_ROUTING_NUMBER': routing_number,
        'MORTGAGE_ACCOUNT_NUMBER': account_number
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}='your_value_here'")
        return False
    
    driver = None
    
    try:
        print("🚀 Starting mortgage payment automation...\n")
        
        # Initialize driver
        print("📱 Setting up Chrome driver...")
        driver = setup_driver()
        
        # Step 1: Navigate to login page
        print("🌐 Navigating to portal.hoaorganizers.com/login...")
        driver.get('https://portal.hoaorganizers.com/login')
        time.sleep(2)
        
        # Step 2: Click "log in with password" button
        print("🔐 Clicking 'Log in with password'...")
        find_and_click(driver, selectors['login_with_password_button'], "'Log in with password' button")
        time.sleep(1)
        
        # Step 3: Enter email
        print(f"📧 Entering email: {email[:3]}***{email[-10:]}...")
        find_and_send_keys(driver, selectors['email_input'], email, "Email field")
        time.sleep(0.5)
        
        # Step 4: Enter password
        print("🔑 Entering password...")
        find_and_send_keys(driver, selectors['password_input'], password, "Password field")
        time.sleep(0.5)
        
        # Step 5: Click login button
        print("✅ Clicking login button...")
        find_and_click(driver, selectors['login_submit_button'], "Login button")
        time.sleep(3)
        
        # Step 6: Click "make online payment"
        print("💰 Clicking 'Make online payment'...")
        find_and_click(driver, selectors['make_payment_button'], "'Make online payment' button")
        time.sleep(2)
        
        # Step 7: Enter phone number
        print(f"📞 Entering phone number: ***-***-{phone[-4:]}...")
        find_and_send_keys(driver, selectors['phone_input'], phone, "Phone number field")
        time.sleep(0.5)
        
        # Step 8: Select "pay by echeck"
        print("🏦 Selecting 'Pay by eCheck'...")
        find_and_click(driver, selectors['echeck_option'], "eCheck payment option")
        time.sleep(1)
        
        # Step 9: Enter routing number
        print(f"🔢 Entering routing number: ***{routing_number[-4:]}...")
        find_and_send_keys(driver, selectors['routing_number_input'], routing_number, "Routing number field")
        time.sleep(0.5)
        
        # Step 10: Enter account number
        print(f"💳 Entering account number: ***{account_number[-4:]}...")
        find_and_send_keys(driver, selectors['account_number_input'], account_number, "Account number field")
        time.sleep(0.5)
        
        # Step 11: Enter account number confirmation (if exists)
        if selectors.get('account_number_confirm_input'):
            print("💳 Confirming account number...")
            find_and_send_keys(driver, selectors['account_number_confirm_input'], account_number, "Account number confirmation field")
            time.sleep(0.5)
        
        # Step 12: Check agreement checkbox
        print("✔️  Checking agreement checkbox...")
        find_and_click(driver, selectors['agreement_checkbox'], "Agreement checkbox")
        time.sleep(1)
        
        # Step 13: Click "Next" button
        print("➡️  Clicking 'Next'...")
        find_and_click(driver, selectors['next_button'], "'Next' button")
        time.sleep(2)
        
        # Step 14: Click "Submit Payment" button
        print("🎯 Clicking 'Submit Payment'...")
        find_and_click(driver, selectors['submit_payment_button'], "'Submit Payment' button")
        time.sleep(3)
        
        # Wait for confirmation
        print("\n⏳ Waiting for payment confirmation...")
        time.sleep(5)
        
        # Check for success message
        try:
            success_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'success') or contains(text(), 'Success') or contains(text(), 'confirmed') or contains(text(), 'Confirmed')]"))
            )
            print("\n✅ ✅ ✅ PAYMENT SUCCESSFUL! ✅ ✅ ✅")
            print(f"Confirmation message: {success_element.text}")
            
        except TimeoutException:
            print("\n⚠️  Could not find confirmation message, but payment may have been submitted.")
            print("Please check your account to verify the payment.")
        
        # Take a screenshot for records
        screenshot_path = f"/tmp/mortgage_payment_{time.strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n📸 Screenshot saved to: {screenshot_path}")
        
        # Wait a bit before closing
        time.sleep(3)
        
        return True
        
    except TimeoutException as e:
        print(f"\n❌ ERROR: Timeout waiting for element: {str(e)}")
        if driver:
            screenshot_path = f"/tmp/mortgage_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Error screenshot saved to: {screenshot_path}")
        return False
        
    except NoSuchElementException as e:
        print(f"\n❌ ERROR: Could not find element: {str(e)}")
        if driver:
            screenshot_path = f"/tmp/mortgage_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Error screenshot saved to: {screenshot_path}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: An unexpected error occurred: {str(e)}")
        if driver:
            screenshot_path = f"/tmp/mortgage_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Error screenshot saved to: {screenshot_path}")
        return False
        
    finally:
        if driver:
            print("\n🧹 Cleaning up...")
            time.sleep(2)
            driver.quit()


if __name__ == '__main__':
    print("=" * 60)
    print("     AUTOMATED MORTGAGE PAYMENT SCRIPT")
    print("=" * 60)
    print()
    
    success = pay_mortgage()
    
    print("\n" + "=" * 60)
    if success:
        print("     ✅ Script completed successfully!")
    else:
        print("     ❌ Script encountered errors")
    print("=" * 60)
