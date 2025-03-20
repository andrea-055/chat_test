# test_chat.py
from playwright.sync_api import Page, expect
import time

def test_send_message(page: Page):
    # 1. Oldal megnyitása
    page.goto("http://65.108.40.58:5173/")

    # 2. Felhasználónév megadása és submit
    page.fill("input[name='name']", "TA_test_user")
    page.click("button[type='submit']")

    # 3. Várakozás a csevegő felület betöltésére
    page.wait_for_load_state("networkidle")  # Várjuk, hogy az oldal stabil legyen
    page.wait_for_selector(".chat-input__input", state="visible", timeout=5000)  # Várjuk az üzenetmezőt

    # 4. Üzenet generálása és elküldése
    test_message = "Test_message " + str(page.evaluate("Date.now()"))  # Egyedi üzenet
    page.fill(".chat-input__input", test_message)
    page.click(".chat-input__send-button")

    # 5. Várjuk a hálózati választ (pl. POST kérés)
    def check_request(request):
        if request.method == "POST" and "soc" in request.url:
            print(f"POST kérés: {request.url}")
    page.on("request", check_request)
    page.wait_for_timeout(5000)  # Várunk a kérésre

    # 6. Ellenőrizzük a "Retry" gombot és az üzenet stabilitását
    start_time = time.time()
    message_appeared = False
    while time.time() - start_time < 40:  # 40 másodperc limit
        if page.query_selector(".retry-button"):
            print("Retry gomb megjelent, üzenetküldés sikertelen!")
            page.screenshot(path="retry_screenshot.png")  # Készítünk screenshotot
            raise Exception("Retry gomb megjelent, teszt sikertelen")
        elif page.evaluate(f"document.querySelector('.messages') && document.querySelector('.messages').innerText.includes('{test_message}')"):
            message_appeared = True
            # Stabilitási ellenőrzés: 30 másodpercig várunk, hogy ne jelenjen meg a Retry gomb
            stability_start = time.time()
            retry_detected = False
            while time.time() - stability_start < 30:
                if page.query_selector(".retry-button"):
                    print("Retry gomb megjelent a stabilitási időszakban!")
                    retry_detected = True
                    page.screenshot(path="retry_screenshot.png")  # Készítünk screenshotot
                    break
                time.sleep(0.1)  # Nagyon sűrű ellenőrzés
            if not retry_detected:
                break  # Ha 30 másodpercig nem jelenik meg a Retry gomb, sikeresnek tekintjük
        time.sleep(0.1)  # Nagyon sűrű ellenőrzés a fő ciklusban
    else:
        if not message_appeared:
            raise Exception("Üzenet nem jelent meg 40 másodpercen belül")
        else:
            raise Exception("Üzenet megjelent, de Retry gomb 30 másodperc elteltével is megjelenhetett")

    # 7. Hibakeresési információ: Nézzük meg az üzenetlista tartalmát
    try:
        messages_content = page.locator(".messages").inner_text(timeout=30000)
        print(f"Üzenetlista tartalma: {messages_content}")
    except Exception as e:
        page.screenshot(path="error_screenshot.png")  # Készít egy screenshotot a hiba esetén
        raise e

    # 8. Ellenőrzés: Megjelenik-e az üzenet
    message_locator = page.locator(".messages .message p.message__right-side__text").filter(has_text=test_message)
    expect(message_locator).to_contain_text(test_message, timeout=20000)

# Futtatás: pytest test_chat.py --headed