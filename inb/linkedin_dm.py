#!/usr/bin/env python3
"""
LinkedIn DM Automation using Selenium with Cookie-based Authentication
Sends direct messages with resume link to connections.
Uses cookies for reliable long-term authentication.
"""

import os
import sys
import json
import time
import argparse
import pandas as pd
import re
import random
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ============================================================
# DAILY LIMITS - Stay under LinkedIn's radar
# ============================================================
DAILY_MESSAGE_LIMIT = 25  # Safe daily limit for messages
DAILY_CONNECTION_LIMIT = 15  # If also sending connection requests
USAGE_FILE = 'linkedin_usage.json'  # Track daily usage


def load_usage():
    """Load daily usage tracking."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    usage_path = os.path.join(script_dir, USAGE_FILE)
    
    if os.path.exists(usage_path):
        with open(usage_path, 'r') as f:
            data = json.load(f)
            # Reset if it's a new day
            if data.get('date') != str(date.today()):
                return {'date': str(date.today()), 'messages': 0, 'connections': 0}
            return data
    return {'date': str(date.today()), 'messages': 0, 'connections': 0}


def save_usage(usage):
    """Save daily usage tracking."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    usage_path = os.path.join(script_dir, USAGE_FILE)
    with open(usage_path, 'w') as f:
        json.dump(usage, f)


def get_remaining_quota(action_type='messages'):
    """Get remaining daily quota for an action type."""
    usage = load_usage()
    if action_type == 'messages':
        return max(0, DAILY_MESSAGE_LIMIT - usage.get('messages', 0))
    elif action_type == 'connections':
        return max(0, DAILY_CONNECTION_LIMIT - usage.get('connections', 0))
    return 0


def increment_usage(action_type='messages', count=1):
    """Increment usage counter."""
    usage = load_usage()
    usage[action_type] = usage.get(action_type, 0) + count
    save_usage(usage)
    return usage


def extract_public_id(linkedin_url):
    """Extract public_id from LinkedIn URL."""
    if not linkedin_url or pd.isna(linkedin_url):
        return None
    match = re.search(r'linkedin\.com/in/([^/?]+)', str(linkedin_url))
    return match.group(1) if match else None


def load_profiles_from_excel(excel_path, limit=20):
    """Load profiles from Excel file that haven't been messaged yet."""
    df = pd.read_excel(excel_path)
    
    # Filter rows where Status doesn't indicate already messaged
    already_done = ['sent', 'messaged', 'dm_sent', 'message_sent']
    unsent = df[~df['Status'].isin(already_done) | df['Status'].isna()]
    
    profiles = []
    for _, row in unsent.head(limit).iterrows():
        public_id = extract_public_id(row.get('Linkedin URL', ''))
        if public_id:
            profiles.append({
                'name': row.get('Name', 'Unknown'),
                'public_id': public_id,
                'company': row.get('Company Name', 'N/A'),
                'linkedin_url': row.get('Linkedin URL', ''),
                'row_index': row.name
            })
    
    return df, profiles


def update_excel_status(excel_path, df, row_index, status, delivered=''):
    """Update the Status and Delivered columns in Excel."""
    df.at[row_index, 'Status'] = status
    if delivered:
        df.at[row_index, 'Delivered'] = delivered
    df.to_excel(excel_path, index=False)


def setup_driver(headless=True):
    """Set up Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def linkedin_login_with_cookie(driver, li_at_cookie):
    """Login to LinkedIn using li_at session cookie."""
    # First visit LinkedIn to set the domain
    driver.get('https://www.linkedin.com')
    time.sleep(2)
    
    # Add the li_at cookie
    driver.add_cookie({
        'name': 'li_at',
        'value': li_at_cookie,
        'domain': '.linkedin.com',
        'path': '/',
        'secure': True,
        'httpOnly': True
    })
    
    # Refresh to apply cookie
    driver.get('https://www.linkedin.com/feed/')
    time.sleep(3)
    
    # Check if logged in
    if 'feed' in driver.current_url or 'mynetwork' in driver.current_url:
        return True
    if 'login' in driver.current_url or 'authwall' in driver.current_url:
        return False
    return True


def linkedin_login_with_password(driver, email, password):
    """Fallback: Login to LinkedIn with email/password."""
    driver.get('https://www.linkedin.com/login')
    time.sleep(2)
    
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        email_field.clear()
        email_field.send_keys(email)
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.clear()
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        
        time.sleep(3)
        
        if 'feed' in driver.current_url or 'mynetwork' in driver.current_url:
            return True
        if 'checkpoint' in driver.current_url or 'challenge' in driver.current_url:
            print("⚠️ Security verification required!")
            return False
        return True
        
    except Exception as e:
        print(f"Login error: {e}")
        return False


def send_dm(driver, public_id, message):
    """
    Send a direct message to a LinkedIn profile.
    Returns: 'sent', 'not_connected', 'error:...'
    """
    profile_url = f'https://www.linkedin.com/in/{public_id}/'
    driver.get(profile_url)
    time.sleep(random.uniform(3, 5))
    
    try:
        # Look for Message button (only visible for connections)
        message_button = None
        
        # Method 1: Direct Message button
        buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="Message"]]')
        if buttons:
            message_button = buttons[0]
        
        # Method 2: aria-label with Message
        if not message_button:
            buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Message")]')
            if buttons:
                message_button = buttons[0]
        
        if not message_button:
            # Not connected - can't send DM
            # Check if we can see Connect button instead
            connect_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Connect"]]')
            if connect_btns:
                return 'not_connected'
            return 'no_message_button'
        
        # Click Message button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", message_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", message_button)
        time.sleep(2)
        
        # Wait for message modal/chat to open
        # Find the message input area
        msg_input = None
        
        # Method 1: contenteditable div in messaging
        inputs = driver.find_elements(By.XPATH, '//div[contains(@class, "msg-form__contenteditable")]')
        if inputs:
            msg_input = inputs[0]
        
        # Method 2: Try textarea
        if not msg_input:
            inputs = driver.find_elements(By.XPATH, '//textarea[contains(@class, "msg-form")]')
            if inputs:
                msg_input = inputs[0]
        
        # Method 3: Generic contenteditable
        if not msg_input:
            inputs = driver.find_elements(By.XPATH, '//div[@contenteditable="true" and contains(@class, "msg")]')
            if inputs:
                msg_input = inputs[0]
        
        if not msg_input:
            return 'no_message_input'
        
        # Type the message
        msg_input.click()
        time.sleep(0.3)
        
        # Clear any existing text and type new message
        msg_input.send_keys(Keys.CONTROL + 'a')
        msg_input.send_keys(Keys.DELETE)
        msg_input.send_keys(message)
        time.sleep(0.5)
        
        # Find and click Send button
        send_button = None
        
        # Method 1: Send button in messaging
        buttons = driver.find_elements(By.XPATH, '//button[contains(@class, "msg-form__send-button")]')
        if buttons:
            send_button = buttons[0]
        
        # Method 2: aria-label Send
        if not send_button:
            buttons = driver.find_elements(By.XPATH, '//button[@type="submit" and contains(@class, "msg")]')
            if buttons:
                send_button = buttons[0]
        
        if not send_button:
            # Try Enter key to send
            msg_input.send_keys(Keys.RETURN)
            time.sleep(1)
            return 'sent_enter'
        
        driver.execute_script("arguments[0].click();", send_button)
        time.sleep(1)
        
        # Close chat window
        try:
            close_btns = driver.find_elements(By.XPATH, '//button[contains(@class, "msg-overlay-bubble-header__control--close")]')
            if close_btns:
                close_btns[0].click()
        except:
            pass
        
        return 'sent'
        
    except Exception as e:
        return f'error: {str(e)[:100]}'


def send_connection_with_note(driver, public_id, note):
    """
    Send a connection request with a note (for non-connections).
    Returns: 'sent', 'already_connected', 'pending', 'error:...'
    """
    profile_url = f'https://www.linkedin.com/in/{public_id}/'
    driver.get(profile_url)
    time.sleep(random.uniform(3, 5))
    
    # Scroll to trigger lazy loading
    driver.execute_script("window.scrollBy(0, 300)")
    time.sleep(1)
    
    try:
        # Check if already connected
        if driver.find_elements(By.XPATH, '//button[.//span[text()="Message"]]'):
            return 'already_connected'
        
        if driver.find_elements(By.XPATH, '//button[.//span[text()="Pending"]]'):
            return 'pending'
        
        # Find Connect button
        connect_button = None
        
        buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="Connect"]]')
        if buttons:
            connect_button = buttons[0]
        
        # Try More menu if no direct Connect
        if not connect_button:
            more_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "More action")]')
            if more_btns:
                driver.execute_script("arguments[0].click();", more_btns[0])
                time.sleep(1)
                connect_items = driver.find_elements(By.XPATH, '//div[contains(@class, "artdeco-dropdown")]//span[text()="Connect"]/..')
                if connect_items:
                    driver.execute_script("arguments[0].click();", connect_items[0])
                    time.sleep(1)
        else:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", connect_button)
            time.sleep(1)
        
        # Handle connection modal - Add note
        add_note_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Add a note")]')
        if add_note_btns:
            driver.execute_script("arguments[0].click();", add_note_btns[0])
            time.sleep(0.5)
            
            textareas = driver.find_elements(By.XPATH, '//textarea[contains(@name, "message") or @id="custom-message"]')
            if textareas:
                textareas[0].clear()
                textareas[0].send_keys(note[:300])
                time.sleep(0.5)
        
        # Click Send
        send_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Send") or .//span[text()="Send"]]')
        if send_btns:
            driver.execute_script("arguments[0].click();", send_btns[0])
            time.sleep(1)
            return 'sent'
        
        return 'no_send_button'
        
    except Exception as e:
        return f'error: {str(e)[:100]}'


def main():
    parser = argparse.ArgumentParser(description='LinkedIn DM Automation with Cookie Auth')
    parser.add_argument('--cookie', help='LinkedIn li_at cookie value for authentication')
    parser.add_argument('--email', help='LinkedIn email (fallback if no cookie)')
    parser.add_argument('--password', help='LinkedIn password (fallback)')
    parser.add_argument('--excel', default='linkedin-data.xlsx', help='Excel file with profiles')
    parser.add_argument('--limit', type=int, default=10, help='Max messages to send (respects daily limit)')
    parser.add_argument('--resume', default='https://drive.google.com/your-resume-link', help='Resume link')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    parser.add_argument('--mode', choices=['dm', 'connect', 'both'], default='dm', 
                        help='dm=message only, connect=connection only, both=try dm first then connect')
    parser.add_argument('--check-quota', action='store_true', help='Just check remaining quota')
    
    args = parser.parse_args()
    
    # Check quota only mode
    if args.check_quota:
        usage = load_usage()
        print("=" * 50)
        print("📊 DAILY QUOTA STATUS")
        print("=" * 50)
        print(f"Date: {usage.get('date', 'N/A')}")
        print(f"Messages sent: {usage.get('messages', 0)} / {DAILY_MESSAGE_LIMIT}")
        print(f"Connections sent: {usage.get('connections', 0)} / {DAILY_CONNECTION_LIMIT}")
        print(f"Messages remaining: {get_remaining_quota('messages')}")
        print(f"Connections remaining: {get_remaining_quota('connections')}")
        return
    
    if not args.cookie and not (args.email and args.password):
        print("❌ Error: Provide --cookie OR --email and --password")
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, args.excel)
    
    # Check remaining quota
    remaining = get_remaining_quota('messages' if args.mode in ['dm', 'both'] else 'connections')
    if remaining == 0:
        print("🚫 Daily limit reached! Try again tomorrow.")
        print(f"   Limit: {DAILY_MESSAGE_LIMIT}/day for messages")
        sys.exit(0)
    
    # Limit to remaining quota
    actual_limit = min(args.limit, remaining)
    
    print("=" * 60)
    print("📨 LINKEDIN DM AUTOMATION (COOKIE AUTH)")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Excel: {args.excel}")
    print(f"Requested: {args.limit} | Available quota: {remaining} | Will process: {actual_limit}")
    print(f"Headless: {args.headless}")
    print(f"Auth: {'Cookie' if args.cookie else 'Password'}")
    print()
    
    # Default message with resume link
    dm_message = f"""Hi! I'm a passionate engineer actively looking for SDE/Full Stack/AI Engineer roles.

I'd really appreciate if you could refer me or share any openings at your company.

📄 Resume: {args.resume}

Thank you so much for your time! 🙏"""

    connection_note = f"""Hi! I'm looking for SDE/AI roles. Would love to connect!
Resume: {args.resume}"""
    
    try:
        # Load profiles
        print(f"📂 Loading profiles from {args.excel}...")
        df, profiles = load_profiles_from_excel(excel_path, actual_limit)
        print(f"📋 Found {len(profiles)} profiles to process\n")
        
        if not profiles:
            print("⚠️ No unprocessed profiles found!")
            return
        
        # Setup browser
        print("🌐 Starting browser...")
        driver = setup_driver(headless=args.headless)
        
        # Login
        print("🔐 Authenticating...")
        if args.cookie:
            if not linkedin_login_with_cookie(driver, args.cookie):
                print("❌ Cookie auth failed, trying password...")
                if args.email and args.password:
                    if not linkedin_login_with_password(driver, args.email, args.password):
                        print("❌ All auth methods failed!")
                        driver.quit()
                        sys.exit(1)
                else:
                    driver.quit()
                    sys.exit(1)
        else:
            if not linkedin_login_with_password(driver, args.email, args.password):
                print("❌ Login failed!")
                driver.quit()
                sys.exit(1)
        
        print("✅ Authenticated!\n")
        
        # Process profiles
        dm_sent = 0
        connect_sent = 0
        failures = 0
        start_time = time.time()
        
        for i, profile in enumerate(profiles, 1):
            name = profile['name']
            public_id = profile['public_id']
            company = profile['company']
            row_index = profile['row_index']
            
            print(f"\n[{i}/{len(profiles)}] {name}")
            print(f"  🏢 {company}")
            print(f"  🔗 {public_id}")
            
            result = None
            
            try:
                if args.mode in ['dm', 'both']:
                    print(f"  📨 Sending DM...")
                    result = send_dm(driver, public_id, dm_message)
                    
                    if result in ['sent', 'sent_enter']:
                        print(f"  ✅ DM sent!")
                        dm_sent += 1
                        increment_usage('messages')
                        update_excel_status(excel_path, df, row_index, 'dm_sent', str(datetime.now()))
                    elif result in ['not_connected', 'no_message_button'] and args.mode == 'both':
                        print(f"  ℹ️ Not connected, sending connection request...")
                        result = send_connection_with_note(driver, public_id, connection_note)
                        if result == 'sent':
                            print(f"  ✅ Connection request sent!")
                            connect_sent += 1
                            increment_usage('connections')
                            update_excel_status(excel_path, df, row_index, 'connect_sent', str(datetime.now()))
                        elif result == 'already_connected':
                            # Try DM again since they are connected
                            print(f"  ℹ️ Already connected, retrying DM...")
                            retry = send_dm(driver, public_id, dm_message)
                            if retry in ['sent', 'sent_enter']:
                                print(f"  ✅ DM sent on retry!")
                                dm_sent += 1
                                increment_usage('messages')
                                update_excel_status(excel_path, df, row_index, 'dm_sent', str(datetime.now()))
                            else:
                                update_excel_status(excel_path, df, row_index, 'connected_no_dm', '')
                        elif result == 'pending':
                            print(f"  ℹ️ Connection already pending")
                            update_excel_status(excel_path, df, row_index, 'pending', '')
                        else:
                            print(f"  ❌ Failed: {result}")
                            failures += 1
                            update_excel_status(excel_path, df, row_index, f'failed:{result[:20]}', '')
                    else:
                        print(f"  ❌ Failed: {result}")
                        failures += 1
                        update_excel_status(excel_path, df, row_index, f'failed:{result[:20]}', '')
                
                elif args.mode == 'connect':
                    print(f"  🔗 Sending connection...")
                    result = send_connection_with_note(driver, public_id, connection_note)
                    
                    if result == 'sent':
                        print(f"  ✅ Connection request sent!")
                        connect_sent += 1
                        increment_usage('connections')
                        update_excel_status(excel_path, df, row_index, 'connect_sent', str(datetime.now()))
                    elif result == 'already_connected':
                        print(f"  ℹ️ Already connected")
                        update_excel_status(excel_path, df, row_index, 'already_connected', '')
                    elif result == 'pending':
                        print(f"  ℹ️ Already pending")
                        update_excel_status(excel_path, df, row_index, 'pending', '')
                    else:
                        print(f"  ❌ Failed: {result}")
                        failures += 1
                        update_excel_status(excel_path, df, row_index, f'failed:{result[:20]}', '')
            
            except Exception as profile_error:
                # Network errors, timeouts, etc - continue with next profile
                print(f"  ❌ Error: {str(profile_error)[:60]}")
                failures += 1
                update_excel_status(excel_path, df, row_index, 'error', str(profile_error)[:40])
            
            # Random delay
            if i < len(profiles):
                delay = random.uniform(8, 15)  # Longer delays for safety
                print(f"  ⏳ Waiting {delay:.1f}s...")
                time.sleep(delay)
        
        driver.quit()
        
        # Summary
        elapsed = time.time() - start_time
        usage = load_usage()
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"📨 DMs sent: {dm_sent}")
        print(f"🔗 Connections sent: {connect_sent}")
        print(f"❌ Failed: {failures}")
        print(f"⏱️ Time: {elapsed:.1f}s")
        print()
        print("📈 Today's usage:")
        print(f"   Messages: {usage.get('messages', 0)} / {DAILY_MESSAGE_LIMIT}")
        print(f"   Connections: {usage.get('connections', 0)} / {DAILY_CONNECTION_LIMIT}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
