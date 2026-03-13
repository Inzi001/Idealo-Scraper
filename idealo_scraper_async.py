import aiohttp
from lxml import html
import asyncio
import json
import csv
from unidecode import unidecode
import re
import os
import time
import gc
import itertools
from datetime import datetime


os.makedirs("json_file", exist_ok=True)



def load_proxies(proxy_file='proxies.txt'):
    with open(proxy_file, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

proxy_cycle = itertools.cycle(load_proxies())

class IDEALO:
    def __init__(self):
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://www.idealo.de/preisvergleich/ProductCategory/4012F1745510I16-15.html?q=smart%20tv',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        
    async def create_session(self):
        proxy_str = next(proxy_cycle)
        proxy_user, proxy_pass_host_port = proxy_str.split(':', 1)
        proxy_pass, proxy_host_port = proxy_pass_host_port.split('@', 1)
        proxy_host, proxy_port = proxy_host_port.split(':')
        
        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        connector = aiohttp.TCPConnector()
        self.session = aiohttp.ClientSession(connector=connector, headers=self.headers, proxy=proxy_url)
    
    async def close_session(self):
        await self.session.close()
    
    async def get_search_results(self, url, max_retries=3, delay=1):
        for attempt in range(max_retries):
            await self.create_session()
            try:
                async with self.session.get(url
                      # Proxy is handled by connector
                ) as response:
                    if response.status == 200:
                        content = await response.read()
                        dom = html.fromstring(content)
                        return dom
                    else:
                        print(f"{response.status} Error: Unable to fetch search results for query '{url}'")
                        return None
            except Exception as e:
                print(f"Attempt {attempt+1}/{max_retries} failed: {e} {url}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    print("All retries failed.")
                    return None, None
            finally:
                await self.close_session()
    
    async def get_product_details(self, EAN, ASIN, product_url):
        print(f"📦 Extracting: {EAN}")   
        if not product_url:
            data = [{
                "ASIN": ASIN,
                "EAN": EAN,
                "ASIN_EAN": f"{ASIN}_{EAN}",
                'product_id': '',
                "product_url": '',
                "product_name": '',
                "lowest_price": '',
                "highest_price": '',
                "avg_price": '',
                "offer_name": '',
                "price": '',
                "price_with_shipping": '',
                "seller_name": '',
                "delivery_date": '',
                "shipping_provider": '',
                "return_policy": '',
                "payment_methods": '',
                "vendor_name": '',
                "product_rating": '',
                "product_rating_count": '',
                "offer_url": '',
                "thumbnail_img_url": '',
                'price_chart': '',
                "images": '',
                "eror": f"„{EAN}“ konnten wir leider nicht finden"
            }]
            return data
        dom = await self.get_search_results(product_url)
        if dom is None:
            data = [{
                "ASIN": ASIN,
                "EAN": EAN,
                "ASIN_EAN": f"{ASIN}_{EAN}",
                'product_id': '',
                "product_url": product_url,
                "product_name": '',
                "lowest_price": '',
                "highest_price": '',
                "avg_price": '',
                "offer_name": '',
                "price": '',
                "price_with_shipping": '',
                "seller_name": '',
                "delivery_date": '',
                "shipping_provider": '',
                "return_policy": '',
                "payment_methods": '',
                "vendor_name": '',
                "product_rating": '',
                "product_rating_count": '',
                "offer_url": '',
                "thumbnail_img_url": '',
                'price_chart': '',
                "images": '',
                "eror": f"„{EAN}“ konnten wir leider nicht finden"
            }]
            return data
        product_id = ''
        script = dom.xpath('//script[@id="tagManagerDataLayer"]/text()')
        if script:
            match = re.search(r'"id"\s*:\s*(\d+)', script[0])
            if match:
                product_id = int(match.group(1))
        
        # Extract product name
        product_name = dom.xpath('//h1[@id="oopStage-title"]/span/text()')
        product_name = product_name[0].strip() if product_name else None

        # Extract product image URL
        thumbnail_img_url = dom.xpath('//img[@class="datasheet-cover-image"]/@src')
        thumbnail_img_url = thumbnail_img_url[0].strip() if thumbnail_img_url else None
        image_urls = dom.xpath('//div[@class="simple-carousel-thumbnail-wrapper"]/img/@src')

        # Get price chart data
        await self.create_session()
        try:
            params = {'period': '3M'}
            async with self.session.get(
                f'https://www.idealo.de/price-chart/sites/1/products/{product_id}/history',
                params=params
            ) as response:
                json_data = await response.json()
                
                with open(f'json_file/{EAN}.json', 'w', encoding='utf-8') as f:
                    json.dump(json_data['data'], f, indent=4, ensure_ascii=False)
                
                avg_price = json_data.get('statistics', {}).get('avgPrice')
                lowest_price = json_data.get('statistics', {}).get('lowestPrice')
                highest_price = json_data.get('statistics', {}).get('highestPrice')
        except Exception as e:
            print(f"Error getting price chart: {e}")
            avg_price = None
            lowest_price = None
            highest_price = None
        finally:
            await self.close_session()

        offers = dom.xpath('//li[contains(@class, "productOffers-listItem")]')
        
        if not offers:
            data = [{
                "ASIN": ASIN,
                "EAN": EAN,
                "product_id": product_id,
                "ASIN_EAN": f"{ASIN}_{EAN}",
                "product_url": product_url,
                "product_name": product_name,
                "lowest_price": lowest_price,
                "highest_price": highest_price,
                "avg_price": avg_price,
                "offer_name": '',
                "price": '',    
                "price_with_shipping": '',
                "seller_name": '',
                "delivery_date": '',    
                "shipping_provider": '',
                "return_policy": '',
                "payment_methods": '',  
                "vendor_name": '',
                "product_rating": '',
                "product_rating_count": '',
                "offer_url": '',
                "thumbnail_img_url": thumbnail_img_url,
                'price_chart': f'{EAN}.json',
                "images": ",".join([f"https:{url}" for url in image_urls]),
                "eror": f"„{EAN}“ konnten wir leider nicht finden"
            }]
            return data

        load_more_exists = bool(dom.xpath("//button[contains(@class, 'productOffers-listLoadMore')]"))
        offerpage_view_id = dom.xpath("//meta[@name='offerpage-view-id']/@content")[0]
        offerlist_view_id = dom.xpath("//span[@data-offerlist-view-id]/@data-offerlist-view-id")[0]

        if load_more_exists:
            await self.create_session()
            try:
                params = {
                    'includeFilters': '0',
                    'excludeFilters': '0',
                    'offerpageViewId': offerpage_view_id,
                    'offerlistViewId': offerlist_view_id,
                }
                url = f"https://www.idealo.de/offerpage/offerlist/product/{product_id}/start/20/sort/default"
                
                async with self.session.get(url, params=params) as more_offers_response:
                    more_offers_content = await more_offers_response.read()
                    more_offers_dom = html.fromstring(more_offers_content)
                    more_offers = more_offers_dom.xpath('//li[contains(@class, "productOffers-listItem")]')
                    offers.extend(more_offers)
            except Exception as e:
                print(f"Error loading more offers: {e}")
            finally:
                await self.close_session()

        base_url = "https://www.idealo.de"
        data = []
        
        for offer in offers:
            title = offer.xpath('.//a[@class="productOffers-listItemTitle"]/span/text()')
            title = title[0].strip() if title else None
            if not title:
                continue

            price = offer.xpath('.//a[contains(@class,"productOffers-listItemOfferPrice")]/text()')
            price = price[0].strip() if price else None
            
            price_shipping = offer.xpath('.//div[contains(@class,"productOffers-listItemOfferShippingDetails")]/text()')
            if not price_shipping:
                price_shipping = offer.xpath('.//div[contains(@class,"productOffers-listItemOfferShippingDetails")]/@title')

            price_shipping = price_shipping[1].strip() if price_shipping else None

            sales_by = offer.xpath('.//div[contains(@class, "productOffers-listItemOfferShopV2MarketPlaceMerchantName")]/a/text()')
            sales_by = sales_by[0].strip() if sales_by else None

            delivery_range = offer.xpath('.//span[contains(@class, "DeliveryStatusDatesRange")]/text()')
            delivery_range = delivery_range[0].strip() if delivery_range else None

            if not delivery_range:
                stock_status = offer.xpath('.//p[contains(@class, "productOffers-listItemOfferDeliveryStatus")]/text()')
                stock_status = [s.strip() for s in stock_status if s.strip()]
                delivery_range = stock_status[0] if stock_status else None

            delivery_date = delivery_range

            shipping_provider = offer.xpath('.//span[contains(@class,"productOffers-listItemOfferDeliveryProvider")]/text()')
            shipping_provider = shipping_provider[0].strip() if shipping_provider else None

            return_policy = offer.xpath('.//div[@class="productOffers-listItemOfferDeliveryRetourText"]/span/text()')
            return_policy = return_policy[0].strip() if return_policy else None

            payment_methods = offer.xpath('.//div[contains(@class, "productOffers-listItemOfferShippingDetailsRight")]//span[contains(@class,"RightItem")]/a/span/text()')
            payment_methods = [pm.strip() for pm in payment_methods if pm.strip()]

            shop_name_data = offer.xpath('./@data-mtrx-click')
            if shop_name_data:
                try:
                    shop_info = json.loads(shop_name_data[0])
                    shop_name = shop_info.get('shop_name')
                except:
                    shop_name = None
            else:
                shop_name = None

            rating = offer.xpath('.//div[contains(@class,"productOffers-listItemOfferShopV2Stars")]//b/text()')
            rating = rating[0] if rating else None

            rating_count = offer.xpath('.//a[contains(@class,"productOffers-listItemOfferShopV2NORatings")]/span/text()')
            rating_count = rating_count[0].strip() if rating_count else None

            offer_url = offer.xpath('.//a[contains(@class,"productOffers-listItemOfferCtaLeadout")]/@href')
            offer_url = base_url + offer_url[0] if offer_url else None

            if title:
                data.append({
                    "ASIN": ASIN,
                    "EAN": EAN,
                    'product_id': product_id,
                    "ASIN_EAN": f"{ASIN}_{EAN}",
                    "product_url": product_url,
                    "product_name": product_name,
                    "lowest_price": lowest_price,
                    "highest_price": highest_price,
                    "avg_price": avg_price,
                    "offer_name": title,
                    "price": price.replace('€', '').replace("Â â¬", "") if price else None,
                    "price_with_shipping": price_shipping.replace('€', '').replace("Â â¬", "") if price_shipping else None,
                    "seller_name": sales_by,
                    "delivery_date": delivery_date,
                    "shipping_provider": shipping_provider,
                    "return_policy": return_policy,
                    "payment_methods": ",".join(payment_methods) if payment_methods else None,
                    "vendor_name": shop_name,
                    "product_rating": rating,
                    "product_rating_count": rating_count,
                    "offer_url": offer_url,
                    "thumbnail_img_url": thumbnail_img_url,
                    'price_chart': f'{EAN}.json',
                    "images": ",".join([f"https:{url}" for url in image_urls]) if image_urls else None,
                    "eror": 'no error'
                })  
        
        gc.collect()    
        return data

async def process_product(row):
    """
    Async function to process a single product.
    """
    idealo = IDEALO()
    try:
        offers = await idealo.get_product_details(row['EAN'], row.get('ASIN'))
        return offers
    except Exception as e:
        print(f"❌ Error processing product {row['EAN']}: {e}")
        return []
    finally:
        if hasattr(idealo, 'session') and idealo.session:
            await idealo.close_session()

async def process_products_concurrently(products, max_concurrent=5):
    """
    Process products concurrently with rate limiting
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_task(row):
        async with semaphore:
            return await process_product(row)
    
    tasks = [limited_task(row) for row in products]
    return await asyncio.gather(*tasks)

def german_to_ascii(text):
    """Convert German special characters to ASCII equivalents"""
    return unidecode(str(text)) if text else ""

async def process_batch(batch, batch_number):
    """Process a single batch with each EAN using a different proxy"""
    print(f"🚀 Starting batch {batch_number} with {len(batch)} EANs")
    
    # Create tasks for each EAN in the batch
    tasks = []
    for i, product in enumerate(batch):
        idealo = IDEALO()  # Each instance will get a different proxy
        tasks.append(asyncio.create_task(
            idealo.get_product_details(product['EAN'], product['ASIN'], product['url']),
            name=f"EAN-{product['EAN']}"
        ))
    
    # Wait for all tasks in this batch to complete
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_results = []
    for result in batch_results:
        if not isinstance(result, Exception):
            successful_results.extend(result)
        else:
            print(f"❌ Error in batch {batch_number}: {str(result)}")
    
    print(f"✅ Finished batch {batch_number}")
    return successful_results

async def process_all_batches(batches):
    """Process all batches with delay between them"""
    all_results = []
    
    for i, batch in enumerate(batches, 1):
        start_time = time.time()
        
        # Process current batch
        batch_results = await process_batch(batch, i)
        all_results.extend(batch_results)
        
        # Calculate time taken and remaining delay
        time_taken = time.time() - start_time
        remaining_delay = max(0, 2 - time_taken)  # Ensure at least 2s between batches
        
        if i < len(batches):  # No need to wait after last batch
            print(f"⏳ Waiting {remaining_delay:.1f}s before next batch...")
            await asyncio.sleep(remaining_delay)
    
    return all_results

async def main():
    products = []
    
    # Read CSV and prepare EAN-ASIN pairs
    with open("new_input_file1.csv", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "EAN": row["EAN"],
                "ASIN": row["ASIN"],
                "url": row["product_url"]
            })

    # Batch into size 22 (1 proxy per EAN)
    batches = [products[i:i+22] for i in range(0, len(products), 22)]
    
    # Process all batches
    all_results = await process_all_batches(batches)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_{timestamp}.csv"
    # Save results
    if all_results:
        keys = all_results[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"💾 Saved {len(all_results)} results to output.csv")
    else:
        print("⚠️ No results to save")

if __name__ == "__main__":
    init=  datetime.now()
    asyncio.run(main())
    final = datetime.now()
    print(final-init)