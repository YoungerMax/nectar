import os
from coupons_api.sources import download_couponsdotcom_coupons, downloading_savingscom_coupons
import asyncio


async def main():
    print('Preparing...')
    os.makedirs('coupons_data', exist_ok=True)

    print('Starting...')
    await downloading_savingscom_coupons()
    await download_couponsdotcom_coupons()


if __name__ == "__main__":
    asyncio.run(main())
