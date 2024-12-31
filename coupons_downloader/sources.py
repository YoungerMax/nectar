import asyncio
import json
import random
from typing import List
import aiofiles
import bs4
import hashlib

import httpx
import tldextract
from coupons_api.types import Coupon, CouponSource, Merchant
from dateutil.parser import parse as parse_date

http_client = httpx.AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
)


async def _get_next_data(url: str):
    await asyncio.sleep(
        random.randrange(5, 20)
    )
    response = await http_client.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    data_tag = soup.find(
        "script", attrs={"id": "__NEXT_DATA__", "type": "application/json"}
    )

    if not data_tag:
        raise RuntimeError(
            '<script id="__NEXT_DATA" type="application/json"> tag not found on: ' + url
        )

    return json.loads(data_tag.text)


async def download_couponsdotcom_coupons():
    print("---coupons.com---")
    COUPONSDOTCOM_SOURCE = CouponSource(
        name="Coupons.com",
        domain="coupons.com",
        is_affiliate_marketing=True,
    )
    data = await _get_next_data("https://www.coupons.com/coupon-codes")

    # Download all merchants
    merchant_ids = []

    for section in data["props"]["pageProps"]["allShops"]:
        for merchant in section[1]:
            merchant_ids.append(
                merchant["url"].replace("coupon-codes", "").replace("/", "")
            )

    # Shuffle the merchants so we're not obviously enumerating their database
    random.shuffle(merchant_ids)

    # Iterate thru merchants
    print(f"Iterating through {len(merchant_ids)} merchants")

    for merchant_id in merchant_ids:
        print(f"Processing merchant: {merchant_id}")

        try:
            merchant_coupons_data = await _get_next_data(
                f"https://www.coupons.com/coupon-codes/{merchant_id}"
            )
        except Exception as e:
            print("Failed", e)
            continue

        coupons: List[Coupon] = []
        merchant_domain = None

        # Convert and add all vouchers
        for voucher in merchant_coupons_data["props"]["pageProps"]["vouchers"]:
            if voucher["type"] != "code":
                continue

            # Parse merchant URL for domain
            merchant_extracted_url = tldextract.extract(voucher["retailer"]["merchantUrl"])
            merchant_domain = merchant_extracted_url.registered_domain

            # Format description
            description = ""

            if voucher["description"]:
                description += voucher["description"] + "\n\n"

            for caption in voucher["termsAndConditions"]["captions"]:
                description += "\n" + caption["key"] + ": " + caption["text"]

            description = description.strip()

            # IDify
            id = "couponsdotcom_" + voucher["idPool"]
            id = hashlib.sha512(id.encode(), usedforsecurity=False).hexdigest()

            # Bring it all together
            coupons.append(
                Coupon(
                    id=id,
                    source=COUPONSDOTCOM_SOURCE,
                    merchant=Merchant(
                        name=voucher["retailer"]["name"],
                        domain=merchant_domain,
                    ),
                    title=voucher["title"],
                    description=description if description else None,
                    expiry=parse_date(voucher["endTime"]).isoformat(),
                    code=voucher["code"],
                )
            )

        if not merchant_domain:
            continue

        # Save the coupons
        async with aiofiles.open(f"coupons_data/{merchant_domain}.json", "wt") as fp:
            serialized = json.dumps([coupon.model_dump() for coupon in coupons])
            await fp.write(serialized)


async def downloading_savingscom_coupons():
    print("---savings.com---")
    response = await http_client.get('https://www.savings.com/sitemap_merchants_1.xml')
    soup = bs4.BeautifulSoup(response.text, 'xml')
    merchant_urls = []

    for loc in soup.find_all('loc'):
        url = loc.text
        
        if url.startswith('https://www.savings.com/coupons/') and '/coupons/stores/' not in url:
            merchant_urls.append(url)

    print(merchant_urls)

    # https://www.savings.com/coupons/
# https://www.savings.com/sitemap_merchants_1.xml
