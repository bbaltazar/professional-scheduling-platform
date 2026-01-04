#!/usr/bin/env python3
"""
Interactive Site Inspector for Mortgage Payment Automation

This script helps you identify the correct element selectors by walking through
the payment process step-by-step. At each step, you'll manually perform the action
while the script shows you what to inspect in the browser's developer tools.

HOW TO USE:
1. Run this script: python scripts/inspect_mortgage_site.py
2. The browser will open and pause at each step
3. Follow the instructions in the terminal
4. Inspect elements using browser DevTools (Right-click → Inspect)
5. Copy the selectors and paste them when prompted
6. The script will save all selectors to mortgage_selectors.json
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def setup_driver():
    """Setup Chrome driver - visible mode for inspection"""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    # Keep browser open for inspection
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)
    return driver


def print_separator():
    print("\n" + "=" * 80)


def print_inspection_guide(step_number, step_name, element_description, example):
    """Print detailed inspection instructions"""
    print_separator()
    print(f"STEP {step_number}: {step_name}")
    print_separator()
    print(f"\n📋 WHAT TO DO:")
    print(f"   {element_description}")
    print(f"\n🔍 HOW TO INSPECT:")
    print(f"   1. Right-click on the element → 'Inspect' (or press F12)")
    print(f"   2. In DevTools, find the HTML tag for this element")
    print(f"   3. Look for one of these attributes:")
    print(f'      • id="..."')
    print(f'      • name="..."')
    print(f'      • class="..."')
    print(f'      • type="..."')
    print(f"      • Or the exact button/link text")
    print(f"\n💡 EXAMPLE:")
    print(f"   {example}")
    print(f"\n✏️  WHAT TO COPY:")
    print(f"   Copy ONE of these (in order of preference):")
    print(f'   1. id="some-id"         → Paste: some-id')
    print(f'   2. name="some-name"     → Paste: some-name')
    print(f"   3. Button text            → Paste: exact text you see")
    print(f"   4. CSS selector           → Paste: .class-name or #id-name")
    print_separator()


def inspect_login_page(driver, selectors):
    """Step 1-2: Navigate and inspect login page"""

    # Navigate to login
    print("\n🌐 Navigating to login page...")
    driver.get("https://portal.hoaorganizers.com/login")
    time.sleep(2)

    # Step 1: Inspect "Log in with password" button
    print_inspection_guide(
        step_number=1,
        step_name="'Log in with password' Button",
        element_description="Find the button/link that says 'Log in with password'",
        example="""
        If you see HTML like:
            <button id="password-login-btn">Log in with password</button>
        
        → Copy: password-login-btn
        → Selector type: id
        
        OR if you see:
            <button class="login-btn">Log in with password</button>
        
        → Copy: Log in with password
        → Selector type: text
        """,
    )

    input(
        "\n⏸️  Press ENTER after you've inspected the 'Log in with password' button..."
    )

    selector_value = input("\n📝 Paste the id/name/text here: ").strip()
    selector_type = input("📝 Selector type (id/name/text/css): ").strip().lower()

    selectors["login_with_password_button"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Button to switch to password login",
    }

    print("\n✅ Saved! Now manually click the button to proceed...")
    input("⏸️  Press ENTER after you've clicked it...")


def inspect_credentials(driver, selectors):
    """Step 2-3: Inspect email and password fields"""

    # Email field
    print_inspection_guide(
        step_number=2,
        step_name="Email Input Field",
        element_description="Find the email/username input field",
        example="""
        If you see HTML like:
            <input type="email" id="email" name="username" />
        
        → Copy: email
        → Selector type: id
        
        OR:
            <input type="text" name="email-address" />
        
        → Copy: email-address
        → Selector type: name
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the email field...")

    selector_value = input("\n📝 Paste the id/name/css here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["email_input"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Email/username input field",
    }

    # Password field
    print_inspection_guide(
        step_number=3,
        step_name="Password Input Field",
        element_description="Find the password input field",
        example="""
        If you see HTML like:
            <input type="password" id="password" name="pass" />
        
        → Copy: password
        → Selector type: id
        
        OR:
            <input type="password" name="user-password" />
        
        → Copy: user-password
        → Selector type: name
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the password field...")

    selector_value = input("\n📝 Paste the id/name/css here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["password_input"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Password input field",
    }

    # Login button
    print_inspection_guide(
        step_number=4,
        step_name="Login Submit Button",
        element_description="Find the button that submits the login form (Sign In / Log In)",
        example="""
        If you see HTML like:
            <button type="submit" id="login-btn">Sign In</button>
        
        → Copy: login-btn
        → Selector type: id
        
        OR:
            <button type="submit">Log In</button>
        
        → Copy: Log In
        → Selector type: text
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the login button...")

    selector_value = input("\n📝 Paste the id/name/text here: ").strip()
    selector_type = input("📝 Selector type (id/name/text/css): ").strip().lower()

    selectors["login_submit_button"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Submit button for login form",
    }

    print("\n✅ Now manually enter your credentials and click login...")
    input("⏸️  Press ENTER after you've logged in and reached the dashboard...")


def inspect_payment_page(driver, selectors):
    """Step 4: Inspect 'Make online payment' link/button"""

    print_inspection_guide(
        step_number=5,
        step_name="'Make Online Payment' Link/Button",
        element_description="Find the link or button to start making a payment",
        example="""
        If you see HTML like:
            <a href="/payment" class="payment-link">Make online payment</a>
        
        → Copy: payment-link
        → Selector type: css (with dot: .payment-link)
        
        OR:
            <button id="make-payment">Make online payment</button>
        
        → Copy: make-payment
        → Selector type: id
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the payment button/link...")

    selector_value = input("\n📝 Paste the id/class/text here: ").strip()
    selector_type = input("📝 Selector type (id/css/text): ").strip().lower()

    selectors["make_payment_button"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Button/link to make online payment",
    }

    print("\n✅ Now manually click 'Make online payment'...")
    input("⏸️  Press ENTER after you've clicked it and the payment form loads...")


def inspect_payment_form(driver, selectors):
    """Step 5-10: Inspect payment form fields"""

    # Phone number
    print_inspection_guide(
        step_number=6,
        step_name="Phone Number Input",
        element_description="Find the phone number input field",
        example="""
        If you see HTML like:
            <input type="tel" name="phone" id="phone-number" />
        
        → Copy: phone-number
        → Selector type: id
        
        OR:
            <input type="text" name="contact-phone" />
        
        → Copy: contact-phone
        → Selector type: name
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the phone field...")

    selector_value = input("\n📝 Paste the id/name here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["phone_input"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Phone number input field",
    }

    # eCheck radio/button
    print_inspection_guide(
        step_number=7,
        step_name="'Pay by eCheck' Option",
        element_description="Find the radio button or option for eCheck payment",
        example="""
        If you see HTML like:
            <input type="radio" name="payment-method" value="echeck" id="echeck-option" />
            <label for="echeck-option">Pay by eCheck</label>
        
        → Copy: echeck-option
        → Selector type: id
        
        OR if it's a button/label to click:
            <label class="payment-option">Pay by eCheck</label>
        
        → Copy: Pay by eCheck
        → Selector type: text
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the eCheck option...")

    selector_value = input("\n📝 Paste the id/value/text here: ").strip()
    selector_type = input("📝 Selector type (id/name/text/css): ").strip().lower()

    selectors["echeck_option"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "eCheck payment method selector",
    }

    print("\n✅ Now manually select 'Pay by eCheck'...")
    input("⏸️  Press ENTER after the eCheck form appears...")

    # Routing number
    print_inspection_guide(
        step_number=8,
        step_name="Routing Number Input",
        element_description="Find the routing number input field",
        example="""
        If you see HTML like:
            <input type="text" name="routing-number" id="routing" />
        
        → Copy: routing
        → Selector type: id
        
        OR:
            <input name="bank-routing" placeholder="Routing number" />
        
        → Copy: bank-routing
        → Selector type: name
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the routing number field...")

    selector_value = input("\n📝 Paste the id/name here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["routing_number_input"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Routing number input field",
    }

    # Account number (first)
    print_inspection_guide(
        step_number=9,
        step_name="Account Number Input (First)",
        element_description="Find the FIRST account number input field",
        example="""
        If you see HTML like:
            <input type="text" name="account-number" id="account-num" />
        
        → Copy: account-num
        → Selector type: id
        
        NOTE: There might be TWO account fields (entry + confirmation).
        We're looking for the FIRST one.
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the account number field...")

    selector_value = input("\n📝 Paste the id/name here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["account_number_input"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Account number input field (first/main)",
    }

    # Account number confirmation
    print_inspection_guide(
        step_number=10,
        step_name="Account Number Confirmation Input (Second)",
        element_description="Find the SECOND account number field (confirmation)",
        example="""
        If you see HTML like:
            <input type="text" name="confirm-account" id="account-confirm" />
        
        → Copy: account-confirm
        → Selector type: id
        
        OR:
            <input name="account-number-verify" />
        
        → Copy: account-number-verify
        → Selector type: name
        
        If there's NO confirmation field, just type: NONE
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the confirmation field...")

    selector_value = input("\n📝 Paste the id/name (or NONE): ").strip()

    if selector_value.upper() != "NONE":
        selector_type = input("📝 Selector type (id/name/css): ").strip().lower()
        selectors["account_number_confirm_input"] = {
            "value": selector_value,
            "type": selector_type,
            "description": "Account number confirmation input field",
        }
    else:
        selectors["account_number_confirm_input"] = None

    # Agreement checkbox
    print_inspection_guide(
        step_number=11,
        step_name="Agreement Checkbox",
        element_description="Find the checkbox for 'I agree to pay...'",
        example="""
        If you see HTML like:
            <input type="checkbox" id="agree-terms" name="agreement" />
            <label for="agree-terms">I agree to pay...</label>
        
        → Copy: agree-terms
        → Selector type: id
        
        OR if you need to click the label:
            <label class="agreement-label">
                <input type="checkbox" />
                I agree to pay...
            </label>
        
        → Copy: agreement-label
        → Selector type: css (with dot: .agreement-label)
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the checkbox...")

    selector_value = input("\n📝 Paste the id/name/class here: ").strip()
    selector_type = input("📝 Selector type (id/name/css): ").strip().lower()

    selectors["agreement_checkbox"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Agreement checkbox or label",
    }

    # Next button
    print_inspection_guide(
        step_number=12,
        step_name="'Next' Button",
        element_description="Find the button to proceed to confirmation (usually 'Next' or 'Continue')",
        example="""
        If you see HTML like:
            <button type="button" id="next-btn">Next</button>
        
        → Copy: next-btn
        → Selector type: id
        
        OR:
            <button class="btn-primary">Next</button>
        
        → Copy: Next
        → Selector type: text
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the Next button...")

    selector_value = input("\n📝 Paste the id/text here: ").strip()
    selector_type = input("📝 Selector type (id/text/css): ").strip().lower()

    selectors["next_button"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Next/Continue button",
    }

    print("\n✅ Now manually fill in the form and click Next...")
    input(
        "⏸️  Press ENTER after you've clicked Next and reached the confirmation page..."
    )


def inspect_confirmation_page(driver, selectors):
    """Step 11: Inspect submit payment button"""

    print_inspection_guide(
        step_number=13,
        step_name="'Submit Payment' Button",
        element_description="Find the final button to submit the payment",
        example="""
        If you see HTML like:
            <button type="submit" id="submit-payment">Submit Payment</button>
        
        → Copy: submit-payment
        → Selector type: id
        
        OR:
            <button class="confirm-btn">Submit Payment</button>
        
        → Copy: Submit Payment
        → Selector type: text
        """,
    )

    input("\n⏸️  Press ENTER after you've inspected the Submit Payment button...")

    selector_value = input("\n📝 Paste the id/text here: ").strip()
    selector_type = input("📝 Selector type (id/text/css): ").strip().lower()

    selectors["submit_payment_button"] = {
        "value": selector_value,
        "type": selector_type,
        "description": "Final submit payment button",
    }

    print("\n⚠️  DO NOT click Submit Payment yet - we're just inspecting!")
    print("The selectors have been saved.")


def save_selectors(selectors):
    """Save all selectors to JSON file"""
    output_file = "scripts/mortgage_selectors.json"

    with open(output_file, "w") as f:
        json.dump(selectors, f, indent=2)

    print_separator()
    print(f"✅ All selectors saved to: {output_file}")
    print_separator()
    print("\nNext steps:")
    print("1. Review the generated mortgage_selectors.json file")
    print("2. Run the updated pay_mortgage.py script (I'll generate it next)")
    print("3. Test the automation!")
    print_separator()


def main():
    """Main inspection workflow"""
    print("\n" + "=" * 80)
    print("     MORTGAGE SITE INSPECTOR")
    print("     Interactive Element Selector Discovery Tool")
    print("=" * 80)
    print("\n📚 This tool will help you find the correct element selectors")
    print("   for automating your mortgage payment.")
    print("\n⚠️  You will manually click through the site while inspecting elements.")
    print("   The browser will stay open - DO NOT close it until finished.")
    print("\n🔧 Make sure you have Chrome DevTools knowledge:")
    print("   • Right-click → Inspect Element")
    print("   • Find id, name, or class attributes")
    print("   • Copy selector values")

    input("\n✅ Press ENTER to start...")

    selectors = {}
    driver = setup_driver()

    try:
        inspect_login_page(driver, selectors)
        inspect_credentials(driver, selectors)
        inspect_payment_page(driver, selectors)
        inspect_payment_form(driver, selectors)
        inspect_confirmation_page(driver, selectors)

        save_selectors(selectors)

        print("\n✅ Inspection complete!")
        print("You can now close the browser window.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Inspection cancelled by user")
        if selectors:
            print("Saving partial selectors...")
            save_selectors(selectors)
    except Exception as e:
        print(f"\n❌ Error during inspection: {e}")
        if selectors:
            print("Saving partial selectors...")
            save_selectors(selectors)

    print("\n👋 Done!")


if __name__ == "__main__":
    main()
