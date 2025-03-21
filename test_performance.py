import pytest
from playwright.async_api import async_playwright
import time
import asyncio
import json
import os
import datetime

# Ensure screenshots directory exists__
os.makedirs("screenshots", exist_ok=True)

async def send_message(page, username, message, is_first_message=False):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if is_first_message:
            await page.fill("input[name='name']", username)
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector(".chat-input__input", state="visible", timeout=10000)

        try:
            await page.fill(".chat-input__input", message, timeout=30000)
        except Exception as e:
            screenshot_path = f"screenshots/{username}_{timestamp}_fill_failed.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"Fill failed: {str(e)}")

        try:
            await page.click(".chat-input__send-button", timeout=30000)
        except Exception as e:
            screenshot_path = f"screenshots/{username}_{timestamp}_click_failed.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"Click failed: {str(e)}")

        try:
            message_sent = await page.wait_for_function(
                f"document.querySelector('.messages').innerText.includes('{message}')",
                timeout=20000
            )
            if not message_sent:
                raise Exception("Message did not appear in chat")
        except Exception as e:
            screenshot_path = f"screenshots/{username}_{timestamp}_appear_failed.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"Appearance failed: {str(e)}")

        print(f"User: {username}, Message: {message} - Success")
        return {"status": "success"}

    except Exception as e:
        print(f"User: {username}, Message: {message} - Failed: {str(e)}")
        return {"status": "failed", "error_message": str(e)}

async def user_task(page, username, num_messages):
    await page.goto("http://65.108.40.58:5173/")
    await page.wait_for_load_state("networkidle")

    results = []
    for i in range(num_messages):
        message = f"{username}_Msg_{i}_"+ str(int(time.time() * 1000))
        try:
            result = await send_message(page, username, message, is_first_message=(i == 0))
            results.append(result)
        except Exception as e:
            print(f"User: {username}, Message: {message}, Error: {str(e)}")
            results.append({"status": "failed", "error_message": str(e)})
        await asyncio.sleep(0.5)
    return results

@pytest.mark.asyncio
@pytest.mark.parametrize("num_users", [10, 30, 50])
async def test_performance(num_users):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = []

        for user_id in range(num_users):
            context = await browser.new_context()
            page = await context.new_page()
            username = f"User_{user_id}"
            tasks.append(user_task(page, username, num_messages=5))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        test_data = []
        total_messages = 0
        failed_messages = 0
        error_types = {"Fill failed": 0, "Click failed": 0, "Appearance failed": 0}

        for user_id, user_results in enumerate(results):
            if isinstance(user_results, Exception):
                print(f"User {user_id} task failed completely: {user_results}")
                total_messages += 5
                failed_messages += 5
                test_data.append({"user": user_id, "status": "failed", "error_message": str(user_results)})
            else:
                for result in user_results:
                    total_messages += 1
                    result_entry = {"user": user_id, "status": result["status"]}
                    if result["status"] == "failed":
                        failed_messages += 1
                        error_msg = result["error_message"]
                        result_entry["error_message"] = error_msg
                        if "Fill failed" in error_msg:
                            error_types["Fill failed"] += 1
                        elif "Click failed" in error_msg:
                            error_types["Click failed"] += 1
                        elif "Appearance failed" in error_msg:
                            error_types["Appearance failed"] += 1
                    test_data.append(result_entry)

        # report summary
        failure_rate = (failed_messages / total_messages) * 100 if total_messages > 0 else 0
        print(f"\nTest with {num_users} users:")
        print(f"Total messages sent: {total_messages}")
        print(f"Failed messages: {failed_messages}")
        print(f"Failure rate: {failure_rate:.2f}%")
        print("Failure breakdown:")
        for error_type, count in error_types.items():
            print(f"  - {error_type}: {count}")

        # JSON
        json_filename = f"test_results_{num_users}_users_{timestamp}.json"
        with open(json_filename, "w") as f:
            json.dump(test_data, f, indent=4)

        await browser.close()

if __name__ == "__main__":
    pytest.main(["-v", __file__])