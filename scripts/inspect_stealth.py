import playwright_stealth
import playwright_stealth.stealth
print(f"Package: {playwright_stealth}")
print(f"Module stealth: {playwright_stealth.stealth}")
print(f"Module sync_api: {playwright_stealth.stealth.sync_api}")
print(f"Dir sync_api: {dir(playwright_stealth.stealth.sync_api)}")
