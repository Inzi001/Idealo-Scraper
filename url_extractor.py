import random
from camoufox.sync_api import Camoufox
from lxml import html
import json
import csv
import os

def load_proxies(file="proxies.txt"):
    proxies = []

    with open(file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            user_pass, host_port = line.split("@")
            username, password = user_pass.split(":")
            host, port = host_port.split(":")

            proxies.append({
                "server": f"http://{host}:{port}",
                "username": username,
                "password": password
            })

    return proxies
    

# --- Proxy Pool ---
PROXIES = load_proxies()

input_csv = "KeepaExport-2026-03-11-ProductFinder.csv"
ean_asin_pairs = []

# Read CSV and prepare EAN-ASIN pairs
with open(input_csv, mode='r', newline='', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    for row in reader:
        ean_field = row.get('Produktcodes: EAN')
        asin = row.get('ASIN', '').strip()
        
        if ean_field:
            # Split if multiple EANs in one cell (comma or space separated)
            eans = [ean.strip() for ean in ean_field.replace(";", ",").replace("|", ",").split(",") if ean.strip()]
            
            for ean in eans:
                ean_asin_pairs.append({"EAN": ean, "ASIN": asin})

print(len(ean_asin_pairs))
# --- EAN List ---
def create_browser(proxy):
    return Camoufox(
        geoip=True,
        proxy=proxy,
        os=random.choice(["windows", "macos", "linux"])
    )

def is_blocked(page):
    html = page.content()
    return ("Sicherheitsprüfung (Spam-Schutz)" in html or "Sorry! Something has gone wrong." in html)

proxy_index = 0
ean_index = 5000
final_result = []

while ean_index < len(ean_asin_pairs):

    proxy = PROXIES[proxy_index]
    print(f"\nUsing proxy: {proxy['server']}")
    # if ean_index>=5000:
    #     break

    try:
        with create_browser(proxy) as browser:
            page = browser.new_page()
            page.goto("https://www.idealo.de/")
            page.wait_for_load_state("domcontentloaded")

            # Remove cookie overlay
            page.evaluate("""
                document.querySelectorAll('#usercentrics-cmp-ui, .uc-overlay, .uc-backdrop')
                    .forEach(el => el.remove());
            """)

            while ean_index < len(ean_asin_pairs):
                

                product = ean_asin_pairs[ean_index]
                print(f"Searching EAN: {product['EAN']}")

                page.goto("https://www.idealo.de/")
                

                search = page.locator("input[name='q']")
                search.fill(product['EAN'])
                page.wait_for_timeout(random.randint(2000, 3000))
                search.press("Enter")

                page.wait_for_selector("body")
                page.wait_for_timeout(random.randint(2000, 3000))

                if is_blocked(page):
                    print("🚫 Blocked! Switching proxy...")
                    proxy_index += 1
                    if proxy_index >= len(PROXIES):
                        raise Exception("All proxies are blocked.")
                    break  # Exit inner loop → rotate proxy

                # Save result
                content = page.content()
                dom = html.fromstring(content)
                if dom.xpath('//h1[@id="oopStage-title"]'):
                    script = dom.xpath('//script[@type="application/ld+json"]/text()')[0]
                    data = json.loads(script) 
                    print("✅ Direct product page found.")
                    final_result.append({
                        'EAN':product['EAN'],
                        'ASIN': product['ASIN'],
                        'product_url':data['url']
                    })
                elif dom.xpath('//div[contains(@class, "sr-resultItemLink_YbJS7")]'):
                    print("🔄 Multiple products found.")
                    product_links = dom.xpath('//div[contains(@class, "sr-resultItemLink_YbJS7")]//a/@href')
                    if product_links:
                        final_result.append({
                            'EAN':product['EAN'],
                            'ASIN': product['ASIN'],
                            'product_url':product_links[0]
                        })
                    else:
                        final_result.append({
                        'EAN':product['EAN'],
                        'ASIN': product['ASIN'],
                        'product_url':None
                    })


                else:
                    final_result.append({
                        'EAN':product['EAN'],
                        'ASIN': product['ASIN'],
                        'product_url':None
                    })
                ean_index += 1
                print(ean_index)
                # if ean_index>=5000:
                #     break

    except Exception as e:
        print("Error:", e)
        proxy_index += 1
        if proxy_index >= len(PROXIES):
            proxy_index = 0
            print("❌ No proxies left.")
            
file_path = "new_input_file1.csv"
keys = final_result[0].keys()

with open(file_path, 'a', newline='', encoding='utf-8') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=keys)

    if os.stat(file_path).st_size == 0:
        writer.writeheader()

    writer.writerows(final_result)

    


