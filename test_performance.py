import pytest
from playwright.async_api import async_playwright
import time
import asyncio
import json
import os

# Ensure screenshots directory exists
os.makedirs("screenshots", exist_ok=True)


async def send_message(page, username, message, is_first_message=False):
    try:
        if is_first_message:
            await page.fill("input[name='name']", username)
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector(".chat-input__input", state="visible", timeout=10000)

        await page.fill(".chat-input__input", message)
        await page.click(".chat-input__send-button")

        # Start timing when the sending indicator appears
        await page.wait_for_selector(".chat-input__sending", state="visible", timeout=10000)
        start_time = time.time()

        # Wait for the sending indicator to disappear (message sent)
        await page.wait_for_selector(".chat-input__sending", state="hidden", timeout=20000)
        end_time = time.time()

        duration = end_time - start_time

        # Check if the Retry button appears
        retry_detected = await page.query_selector("button.retry-button")

        if retry_detected:
            screenshot_path = f"screenshots/{username}_failed.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"Message sending failed: Retry button appeared for message: {message}")

        # Verify that the message is actually displayed in the chat
        message_sent = await page.wait_for_function(f"document.querySelector('.messages').innerText.includes('{message}')", timeout=20000)

        if not message_sent:
            screenshot_path = f"screenshots/{username}_failed.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"Message did not appear in chat: {message}")

        print(f"User: {username}, Message: {message}, Sending and display time: {duration:.2f} seconds")
        return duration

    except Exception as e:
        screenshot_path = f"screenshots/{username}_error.png"
        await page.screenshot(path=screenshot_path)
        print(f"Error for User {username}: {str(e)}, Screenshot saved at {screenshot_path}")
        raise e

async def user_task(page, username, num_messages):
    await page.goto("http://65.108.40.58:5173/")
    await page.wait_for_load_state("networkidle")

    durations = []
    for i in range(num_messages):
        message = f"{username}_Msg_{i}_" + str(int(time.time() * 1000))
        try:
            duration = await send_message(page, username, message, is_first_message=(i == 0))
            durations.append(duration)
        except Exception as e:
            print(f"User: {username}, Message: {message}, Error: {str(e)}")
            raise e
        await asyncio.sleep(0.5)
    return durations

@pytest.mark.asyncio
async def test_performance():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        num_users = 5
        tasks = []

        for user_id in range(num_users):
            context = await browser.new_context()
            page = await context.new_page()
            username = f"User_{user_id}"
            tasks.append(user_task(page, username, num_messages=5))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        test_data = []

        for user_id, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"User_{user_id} message sending failed: {str(result)}")
                test_data.append({"user": user_id, "error": str(result)})
            else:
                durations = result
                average_duration = sum(durations) / len(durations)
                print(f"User_{user_id} average sending and display time: {average_duration:.2f} seconds")
                test_data.append({"user": user_id, "average_time": average_duration, "message_count": len(durations)})

        # Save results to JSON
        with open("test_results.json", "w") as f:
            json.dump(test_data, f, indent=4)

        await browser.close()
