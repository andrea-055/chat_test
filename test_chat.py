# test_chat.py
from playwright.sync_api import Page, expect
import time

def test_send_message(page: Page):
    # 1. Navigate to the chat application
    page.goto("http://65.108.40.58:5173/")

    # 2. Enter username and submit
    page.fill("input[name='name']", "TA_test_user")
    page.click("button[type='submit']")

    # 3. Wait for the page to fully load and the chat input to be visible
    page.wait_for_load_state("networkidle")  # Wait for network to be idle
    page.wait_for_selector(".chat-input__input", state="visible", timeout=5000)  # Wait for chat input to be visible

    # 4. Create a unique test message with a timestamp
    test_message = "Test_message " + str(page.evaluate("Date.now()"))  # Unique message with timestamp
    page.fill(".chat-input__input", test_message)
    page.click(".chat-input__send-button")

    # 5. Monitor POST requests and wait for a short period
    def check_request(request):
        if request.method == "POST" and "soc" in request.url:
            print(f"POST request: {request.url}")
    page.on("request", check_request)
    page.wait_for_timeout(5000)  # Wait 5 seconds to allow the request to process

    # 6. Check if the message appears and monitor for retry button
    start_time = time.time()
    message_appeared = False
    while time.time() - start_time < 40:  # Wait up to 40 seconds for the message to appear
        if page.query_selector(".retry-button"):
            print("Retry button appeared, message sending failed!")
            page.screenshot(path="retry_screenshot.png")  # Take a screenshot if retry button appears
            raise Exception("Retry button appeared, test failed")
        elif page.evaluate(f"document.querySelector('.messages') && document.querySelector('.messages').innerText.includes('{test_message}')"):
            message_appeared = True
            # Start stability check for 30 seconds to ensure no retry button appears
            stability_start = time.time()
            retry_detected = False
            while time.time() - stability_start < 30:
                if page.query_selector(".retry-button"):
                    print("Retry button appeared during stability period!")
                    retry_detected = True
                    page.screenshot(path="retry_screenshot.png")  # Take a screenshot if retry button appears
                    break
                time.sleep(0.1)  # Short sleep to avoid excessive CPU usage
            if not retry_detected:
                break  # Exit loop if message appeared and no retry button was detected
        time.sleep(0.1)  # Short sleep to avoid excessive CPU usage
    else:
        if not message_appeared:
            raise Exception("Message did not appear within 40 seconds")
        else:
            raise Exception("Message appeared, but Retry button may have appeared after 30 seconds")

    # 7. Retrieve and print the content of the message list
    try:
        messages_content = page.locator(".messages").inner_text(timeout=30000)
        print(f"Message list content: {messages_content}")
    except Exception as e:
        page.screenshot(path="error_screenshot.png")  # Take a screenshot if an error occurs
        raise e

    # 8. Verify that the message appears in the chat
    message_locator = page.locator(".messages .message p.message__right-side__text").filter(has_text=test_message)
    expect(message_locator).to_contain_text(test_message, timeout=20000)

#