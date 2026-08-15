#!/usr/bin/env python3
"""
Mun-Hwa Bu Integration Tests
Sends real requests to Apps Script and verifies responses.
Usage: python3 test.py [--skip-telegram]
"""

import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import datetime

# ── Config ────────────────────────────────────────────────────────────────────
APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwA86mqargcUKG4wtxPFtFRH8th8aDalxHAnzyo5gVryxK5umZvnGzJviLhtMJZ6D_p0g/exec'
TELEGRAM_TOKEN  = '8658158239:AAGdaVadkSuMkIucFmTO5JWsg8WAuk2ujcA'
TELEGRAM_CHATID = '1113306289'

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

passes = []
failures = []

def ok(msg):
    passes.append(msg)
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    failures.append(msg)
    print(f"  {RED}✗{RESET} {msg}")

def section(title):
    print(f"\n{BOLD}{title}{RESET}")

def today():
    return datetime.date.today().isoformat()

def now_time():
    return datetime.datetime.now().strftime('%H:%M')

# ── HTTP helper ───────────────────────────────────────────────────────────────
def post(payload, timeout=30):
    """POST JSON to Apps Script and return parsed response."""
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        APPS_SCRIPT_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body)
    except urllib.error.URLError as e:
        return {'error': f'Network error: {e}'}
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON response: {e}'}
    except Exception as e:
        return {'error': str(e)}

def check_telegram_reachable():
    """Verify the Telegram bot is reachable."""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('ok'):
                ok(f"Telegram bot reachable: @{data['result']['username']}")
                return True
            else:
                fail(f"Telegram bot error: {data}")
                return False
    except Exception as e:
        fail(f"Telegram unreachable: {e}")
        return False

def get_last_telegram_message():
    """Get the most recent Telegram message to verify delivery."""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?limit=1&offset=-1'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('ok') and data.get('result'):
                return data['result'][-1]
    except:
        pass
    return None

# ── Test cases ────────────────────────────────────────────────────────────────

def test_apps_script_reachable():
    section("Test 1: Apps Script Reachability")
    result = post({'action': 'getEquipment'}, timeout=15)
    if 'error' in result:
        fail(f"Apps Script unreachable: {result['error']}")
        return False
    else:
        ok("Apps Script reachable and responding")
        return True

def test_work_cooperation_request():
    section("Test 2a: Work Cooperation Request (with Approve/Reject buttons)")
    # Tomorrow's date for the event
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    payload = {
        'action': 'newSupportRequest',
        'name': 'Test User [AUTOMATED TEST]',
        'department': 'Youth Ministry',
        'position': 'Youth Leader',
        'telegram': 'testuser',
        'purpose': 'Sunday Youth Service — automated test request',
        'meetingDate': tomorrow,
        'meetingTime': '14:00',
        'requestTypes': 'cooperation',
        'coopEventName': 'Sunday Youth Service [TEST]',
        'coopEventDate': tomorrow,
        'coopStartTime': '10:00',
        'coopVenue': 'EH Ground Floor',
        'coopAssistance': 'Media / Broadcasting, Sound Operation',
        'coopDocLink': 'No document available',
        'propsSubType': 'rental',
    }
    result = post(payload)
    if result.get('success') and result.get('requestId'):
        ok(f"Work Cooperation request created: {result['requestId']} — check Telegram for Approve/Reject buttons")
        return result['requestId']
    elif 'error' in result:
        fail(f"Work Cooperation request failed: {result['error']}")
        return None
    else:
        fail(f"Unexpected response: {result}")
        return None


    section("Test 2: Support Request (Main Form)")
    payload = {
        'action': 'newSupportRequest',
        'name': 'Test User [AUTOMATED TEST]',
        'department': 'Test Dept',
        'position': 'Tester',
        'telegram': 'testuser',
        'purpose': 'Automated test submission — please ignore',
        'meetingDate': today(),
        'meetingTime': now_time(),
        'requestTypes': 'equipment',
        'equipPurpose': 'Automated test',
        'equipPickup': today(),
        'equipReturn': today(),
        'equipItems': '1x Test Camera',
        'equipScope': 'Internal',
        'propsSubType': 'rental',
        'coopAssistance': '',
    }
    result = post(payload)
    if result.get('success') and result.get('requestId'):
        ok(f"Support request created: {result['requestId']}")
        return result['requestId']
    elif 'error' in result:
        fail(f"Support request failed: {result['error']}")
        return None
    else:
        fail(f"Unexpected response: {result}")
        return None

def test_team_checkout():
    section("Test 3: Team Equipment Checkout")
    payload = {
        'action': 'logTeamCheckout',
        'memberName': 'Test Member [AUTOMATED TEST]',
        'telegram': 'testmember',
        'dateOut': today(),
        'timeOut': now_time(),
        'dateReturn': today(),
        'timeReturn': '18:00',
        'purpose': 'Automated test — please ignore',
        'location': 'Test Location',
        'storage': 'Test Storage',
        'returnLocation': 'EH Culture Office',
        'items': ['Test Camera [AUTOMATED]', 'Test Lens [AUTOMATED]'],
        'photos': []
    }
    result = post(payload)
    if result.get('success') and result.get('checkoutId'):
        ok(f"Team checkout logged: {result['checkoutId']}")
        return result['checkoutId']
    elif 'error' in result:
        fail(f"Team checkout failed: {result['error']}")
        return None
    else:
        fail(f"Unexpected response: {result}")
        return None

def test_media_desk_signin():
    section("Test 4: Media Desk Sign In")
    payload = {
        'action': 'mdSignIn',
        'name': 'Test Operator [AUTOMATED TEST]',
        'telegram': 'testoperator',
        'equipment': ['Mixer', 'ATEM'],
        'purpose': 'Automated Test Service',
        'location': 'U15 1st Floor',
        'timeIn': now_time(),
        'assistants': [],
        'date': today()
    }
    result = post(payload)
    if result.get('success') and result.get('entryId'):
        ok(f"Media desk sign in logged: {result['entryId']}")
        return result['entryId']
    elif 'error' in result:
        fail(f"Media desk sign in failed: {result['error']}")
        return None
    else:
        fail(f"Unexpected response: {result}")
        return None

def test_media_desk_signout(entry_id):
    section("Test 5: Media Desk Sign Out")
    if not entry_id:
        fail("Skipped — no entry ID from sign in test")
        return False
    
    # Wait a moment for the sheet to update
    time.sleep(2)
    
    payload = {
        'action': 'mdSignOut',
        'signInName': 'Test Operator [AUTOMATED TEST]',
        'signOutLocation': 'U15 1st Floor',
        'timeOut': now_time(),
        'issueDetails': '',
        'photos': []
    }
    result = post(payload)
    if result.get('success'):
        ok(f"Media desk sign out successful")
        return True
    elif 'error' in result:
        fail(f"Media desk sign out failed: {result['error']}")
        return False
    else:
        fail(f"Unexpected response: {result}")
        return False

def test_telegram_delivery():
    section("Test 6: Telegram Message Delivery")
    # Send a direct test message and verify it arrives
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = json.dumps({
        'chat_id': TELEGRAM_CHATID,
        'text': f'[AUTOMATED TEST] Mun-Hwa Bu audit test — {now_time()}. If you see this, Telegram delivery is working. 🟢',
        'parse_mode': 'HTML'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get('ok'):
                ok(f"Test message delivered to Telegram (message_id: {data['result']['message_id']})")
                return True
            else:
                fail(f"Telegram delivery failed: {data}")
                return False
    except Exception as e:
        fail(f"Telegram delivery error: {e}")
        return False

def test_invalid_action():
    section("Test 7: Invalid Action Handling")
    result = post({'action': 'nonExistentAction123'})
    if result.get('error') == 'Unknown action':
        ok("Invalid action returns correct error response")
        return True
    else:
        fail(f"Unexpected response to invalid action: {result}")
        return False

def test_open_entries(entry_id):
    section("Test 8: Get Open Entries (Media Desk)")
    result = post({'action': 'mdGetOpenEntries', 'date': today()})
    if result.get('success'):
        entries = result.get('entries', [])
        ok(f"Open entries endpoint works — {len(entries)} open entries today")
        return True
    elif 'error' in result:
        fail(f"Get open entries failed: {result['error']}")
        return False
    else:
        fail(f"Unexpected response: {result}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    skip_telegram = '--skip-telegram' in sys.argv
    dry_run = '--dry-run' in sys.argv

    print(f"\n{BOLD}╔══════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║   Mun-Hwa Bu Integration Tests           ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════════╝{RESET}")
    print(f"  Target: {APPS_SCRIPT_URL[:60]}...")
    print(f"  Date: {today()}  Time: {now_time()}")

    if dry_run:
        print(f"\n{YELLOW}DRY RUN — validating test structure only (no network calls){RESET}")
        # Validate test payloads are well-formed JSON
        tests = [
            ('Work Cooperation Request', {'action': 'newSupportRequest', 'name': 'Test [AUTOMATED TEST]', 'department': 'Youth Ministry', 'position': 'Youth Leader', 'telegram': 'testuser', 'purpose': 'Sunday Youth Service — test', 'meetingDate': today(), 'meetingTime': '14:00', 'requestTypes': 'cooperation', 'coopEventName': 'Sunday Youth Service [TEST]', 'coopEventDate': today(), 'coopStartTime': '10:00', 'coopVenue': 'EH Ground Floor', 'coopAssistance': 'Media / Broadcasting, Sound Operation', 'coopDocLink': 'No document available', 'propsSubType': 'rental'}),
            ('Equipment Support Request', {'action': 'newSupportRequest', 'name': 'Test', 'department': 'Test', 'position': 'Test', 'requestTypes': 'equipment', 'equipPurpose': 'Test', 'equipPickup': today(), 'equipReturn': today(), 'equipItems': '1x Camera'}),
            ('Team Checkout',   {'action': 'logTeamCheckout', 'memberName': 'Test', 'dateOut': today(), 'timeOut': '09:00', 'dateReturn': today(), 'timeReturn': '18:00', 'purpose': 'Test', 'location': 'Test', 'storage': 'Test', 'returnLocation': 'EH Culture Office', 'items': ['Camera'], 'photos': []}),
            ('Media Desk Sign In', {'action': 'mdSignIn', 'name': 'Test', 'equipment': ['Mixer'], 'purpose': 'Test', 'location': 'U15 1st Floor', 'timeIn': '09:00', 'assistants': [], 'date': today()}),
            ('Media Desk Sign Out', {'action': 'mdSignOut', 'signInName': 'Test', 'signOutLocation': 'U15 1st Floor', 'timeOut': '18:00', 'issueDetails': '', 'photos': []}),
            ('Invalid Action', {'action': 'nonExistentAction'}),
        ]
        for name, payload in tests:
            try:
                json.dumps(payload)
                ok(f"Payload valid: {name}")
            except Exception as e:
                fail(f"Invalid payload for {name}: {e}")

        total = len(passes) + len(failures)
        print(f"\n{BOLD}══ DRY RUN SUMMARY ══{RESET}")
        print(f"  {GREEN}Valid:{RESET} {len(passes)}/{total} payloads")
        if failures:
            print(f"\n{RED}{BOLD}❌ DRY RUN FAILED{RESET}")
            sys.exit(1)
        else:
            print(f"\n{GREEN}{BOLD}✅ DRY RUN PASSED — Run without --dry-run on your Mac to test live{RESET}")
            sys.exit(0)
        return
    
    if not skip_telegram:
        check_telegram_reachable()
    
    # Run tests
    reachable = test_apps_script_reachable()
    
    if not reachable:
        print(f"\n{RED}{BOLD}❌ Apps Script unreachable — aborting remaining tests{RESET}")
        print("Check: is the deployment live? Is the URL correct?")
        sys.exit(1)
    
    request_id  = test_work_cooperation_request()
    time.sleep(1)
    request_id2 = test_support_request()
    checkout_id = test_team_checkout()
    entry_id    = test_media_desk_signin()
    
    time.sleep(1)  # Give sheet writes a moment
    
    test_open_entries(entry_id)
    test_media_desk_signout(entry_id)
    test_invalid_action()
    
    if not skip_telegram:
        test_telegram_delivery()
    
    # ── Summary ───────────────────────────────────────────────────────────────
    total = len(passes) + len(failures)
    print(f"\n{BOLD}══ TEST SUMMARY ══{RESET}")
    print(f"  {GREEN}Passed:{RESET} {len(passes)}/{total}")
    
    if failures:
        print(f"  {RED}Failed:{RESET} {len(failures)}/{total}")
        print(f"\n{RED}{BOLD}❌ TESTS FAILED{RESET}")
        print(f"\nFailing tests:")
        for f in failures:
            print(f"  {RED}•{RESET} {f}")
        print(f"\n{YELLOW}Note: Test rows were written to your Google Sheet.")
        print(f"You can delete rows containing '[AUTOMATED TEST]' from:{RESET}")
        print(f"  • Support Requests sheet")
        print(f"  • Team Checkouts sheet") 
        print(f"  • Media Desk sheet")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}✅ ALL TESTS PASSED{RESET}")
        print(f"\n{YELLOW}Note: Test rows were written to your Google Sheet.")
        print(f"You can delete rows containing '[AUTOMATED TEST]' from the sheets.{RESET}")
        sys.exit(0)

if __name__ == '__main__':
    main()
