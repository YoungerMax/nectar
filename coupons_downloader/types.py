from pydantic import BaseModel


class CouponSource(BaseModel):
    name: str
    domain: str
    is_affiliate_marketing: bool


class Merchant(BaseModel):
    name: str
    domain: str


class Coupon(BaseModel):
    id: str
    title: str
    description: str | None
    expiry: str
    code: str
    source: CouponSource
    merchant: Merchant
