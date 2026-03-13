# Idealo Product Scraper

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Async](https://img.shields.io/badge/Async-aiohttp-green)
![Scraping](https://img.shields.io/badge/Web%20Scraping-Idealo-orange)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A **high-performance Idealo product scraper** that extracts product offers, seller information, and price history using **EAN and ASIN numbers**.

The project uses a **two-stage scraping pipeline** to efficiently collect product data from Idealo.

---

# 🚀 Features

* Extract product URLs using **EAN numbers**
* Scrape **product offers and seller data**
* Retrieve **price history**
* Async scraping with **aiohttp**
* **Proxy rotation** support
* **Batch processing**
* CSV and JSON output
* Automatic retry handling
* Scalable scraping pipeline

---

# 🧠 Architecture

```
Keepa Export CSV
      │
      ▼
url_extractor.py
(EAN → Idealo Product URL)
      │
      ▼
new_input_file1.csv
(EAN | ASIN | product_url)
      │
      ▼
idealo_scraper_async.py
(Async scraping)
      │
      ▼
Extracted Data
│
├── Product details
├── Seller offers
├── Price statistics
└── Price history JSON
      │
      ▼
Final Output CSV
```

---

# 📂 Project Structure

```
project/
│
├── url_extractor.py
├── idealo_scraper_async.py
├── proxies.txt
├── new_input_file1.csv
│
├── json_file/
│   └── price history json files
│
└── output_YYYYMMDD_HHMMSS.csv
```

---

# 🔎 Step 1 — Extract Product URLs

File:

```
url_extractor.py
```

This script reads a **Keepa export CSV file** and extracts:

* EAN numbers
* ASIN numbers

Using the EAN number, the script searches Idealo and retrieves the **product URL**.

### Input Example

| ASIN   | Produktcodes: EAN |
| ------ | ----------------- |
| B08XYZ | 1234567890123     |

### Output

```
new_input_file1.csv
```

| EAN           | ASIN   | product_url               |
| ------------- | ------ | ------------------------- |
| 1234567890123 | B08XYZ | https://www.idealo.de/... |

---

# ⚡ Step 2 — Async Product Scraper

File:

```
idealo_scraper_async.py
```

This script reads the generated CSV file and scrapes product details from Idealo.

The scraper uses:

* **asyncio**
* **aiohttp**
* **rotating proxies**

to achieve high performance.

---

# 📊 Extracted Data

### Product Data

* product_id
* product_name
* product_url
* thumbnail image
* additional images
* product rating
* rating count

### Price Statistics

* lowest price
* highest price
* average price

### Seller Offer Data

For each seller offer:

* offer title
* price
* price with shipping
* seller name
* vendor name
* delivery date
* shipping provider
* return policy
* payment methods
* offer URL

---

# 📈 Price History

Price history is extracted from Idealo's API and stored as:

```
json_file/{EAN}.json
```

Example:

```
json_file/
 ├── 4002515485455.json
 ├── 1234567890123.json
```

---

# 🔄 Proxy Support

The scraper uses rotating proxies to avoid blocking.

Create a file:

```
proxies.txt
```

Format:

```
username:password@host:port
```

Example:

```
user1:pass1@1.2.3.4:8000
user2:pass2@1.2.3.5:8000
```

---

# ⚙️ Concurrency Model

The scraper processes products in **batches**.

| Parameter   | Value           |
| ----------- | --------------- |
| Batch Size  | 22 products     |
| Concurrency | Async tasks     |
| Proxy Usage | 1 proxy per EAN |
| Batch Delay | 2 seconds       |

---

# 📊 Performance

Example scraping performance:

| Products | Time        |
| -------- | ----------- |
| 100      | ~2 minutes  |
| 1000     | ~15 minutes |
| 5000     | ~1 hour     |

Performance depends on:

* proxy quality
* network speed
* Idealo response time

---

# ⚡ Scraper Comparison

| Method          | Speed         | Blocking Risk |
| --------------- | ------------- | ------------- |
| Selenium        | Slow          | Medium        |
| Playwright      | Medium        | Medium        |
| Async (aiohttp) | **Very Fast** | Low           |

This project uses **async scraping**, making it significantly faster.

---

# 🛠 Installation

Install dependencies:

```
pip install aiohttp lxml unidecode camoufox
```

---

# ▶️ How to Run

### Step 1 — Extract URLs

```
python url_extractor.py
```

Generates:

```
new_input_file1.csv
```

---

### Step 2 — Run Scraper

```
python idealo_scraper_async.py
```

Outputs:

```
output_YYYYMMDD_HHMMSS.csv
```

---

# 📌 Example Output

| EAN           | ASIN   | product_name     | price | seller |
| ------------- | ------ | ---------------- | ----- | ------ |
| 1234567890123 | B08XYZ | Samsung Smart TV | 599   | Amazon |

---

# 🧑‍💻 Author

Web Scraping Engineer
Python • Async Scraping • Data Extraction

---

# ⭐ Use Cases

This scraper can be used for:

* Price monitoring
* Competitor analysis
* Market research
* Seller comparison
* Historical price tracking

---

# ⚠️ Disclaimer

This project is for **educational and research purposes only**.
Please ensure compliance with the target website's **terms of service**.
