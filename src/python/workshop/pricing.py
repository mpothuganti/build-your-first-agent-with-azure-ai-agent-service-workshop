import aiosqlite
import boto3
import json
from typing import Optional, Dict, Any

# Minimal mapping region -> Pricing API location name (expand as needed)
REGION_TO_LOCATION = {
    "us-east-1": "US East (N. Virginia)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "EU (Ireland)",
}


class InstancePricing:
    """
    Fetch on-demand hourly pricing for a single EC2 instance.

    - Mirrors CpuMetrics style: class with an optional DB connection attribute and
      a synchronous method `get_instance_price(instance_id, region, ...) -> str`.
    - Does NOT call EC2 DescribeInstances. If `instance_type` is not supplied
      the class will attempt to locate instance metadata in the repo datasheet.
    """

    def __init__(self: "InstancePricing") -> None:
        self.conn: Optional[aiosqlite.Connection] = None

    def _region_to_location(self: "InstancePricing", region: str) -> str:
        return REGION_TO_LOCATION.get(region, region)

    def _query_price(self: "InstancePricing", instance_type: str, region: str, operating_system: str = "Linux", tenancy: str = "Shared", currency: str = "USD") -> Optional[float]:
        location = self._region_to_location(region)
        filters = [
            {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
            {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": operating_system},
            {"Type": "TERM_MATCH", "Field": "tenancy", "Value": tenancy},
            {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
            {"Type": "TERM_MATCH", "Field": "location", "Value": location},
        ]

        try:
            pricing = boto3.client("pricing", region_name="us-east-1")
        except Exception:
            return None

        candidates = []
        next_token = None
        try:
            while True:
                if next_token:
                    resp = pricing.get_products(ServiceCode="AmazonEC2", Filters=filters, MaxResults=100, NextToken=next_token)
                else:
                    resp = pricing.get_products(ServiceCode="AmazonEC2", Filters=filters, MaxResults=100)

                for pstr in resp.get("PriceList", []):
                    try:
                        prod = json.loads(pstr)
                    except Exception:
                        continue
                    terms = prod.get("terms", {})
                    ondemand = terms.get("OnDemand", {})
                    for od in ondemand.values():
                        for pd in od.get("priceDimensions", {}).values():
                            price_map = pd.get("pricePerUnit", {})
                            price_str = price_map.get(currency) or next(iter(price_map.values()), None)
                            if not price_str:
                                continue
                            try:
                                price = float(price_str)
                            except Exception:
                                continue
                            unit = (pd.get("unit") or "").lower()
                            if "hour" in unit or "hr" in unit:
                                candidates.append(price)
                            else:
                                candidates.append(price)

                next_token = resp.get("NextToken")
                if not next_token:
                    break
        except Exception:
            return None

        if not candidates:
            return None
        return round(max(candidates), 6)

    def get_instance_price(self: "InstancePricing", instance_id: str, region: str = "us-east-1", instance_type: Optional[str] = None, operating_system: Optional[str] = None, tenancy: Optional[str] = None) -> str:
        """
        Fetch price for the instance. This method does NOT load any local datasheet
        or make EC2 DescribeInstances calls. The caller must provide `instance_type`.

        Returns a JSON string similar to CpuMetrics.get_cpu_usage.
        """
        # Require instance_type from caller — we will not read local datasheets
        # or make EC2 DescribeInstances calls. The caller must provide `instance_type`.
        if not instance_type:
            return json.dumps({
                "instance_id": instance_id,
                "instance_type": None,
                "region": region,
                "price_per_hour": None,
                "currency": None,
                "message": "Instance type is required. This method does not load local datasheets or call DescribeInstances. Please provide `instance_type`.",
            })

        # normalize operating_system and tenancy
        if not operating_system:
            operating_system = "Linux"
        if not tenancy:
            tenancy = "Shared"

        price = self._query_price(instance_type, region, operating_system=operating_system, tenancy=tenancy)
        currency = "USD"

        if price is None:
            return json.dumps({
                "instance_id": instance_id,
                "instance_type": instance_type,
                "region": region,
                "price_per_hour": None,
                "currency": None,
                "message": "No pricing entry found or Pricing API error",
            })

        return json.dumps({
            "instance_id": instance_id,
            "instance_type": instance_type,
            "region": region,
            "price_per_hour": price,
            "currency": currency,
            "message": "OK",
        })


def get_instance_price(instance_id: str, region: str = "us-east-1", instance_type: Optional[str] = None, operating_system: Optional[str] = None, tenancy: Optional[str] = None) -> str:
    """
    Module-level wrapper so this functionality can be exposed as a standalone
    function (for function-calling frameworks). Delegates to
    `InstancePricing.get_instance_price`.
    """
    ip = InstancePricing()
    return ip.get_instance_price(instance_id=instance_id, region=region, instance_type=instance_type, operating_system=operating_system, tenancy=tenancy)
