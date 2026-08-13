"""Honesty tokens for the factory / RMA / support STREAM."""

PRODUCTION_RELEASE_CLAIMED = False
COMMERCIAL_WARRANTY = "EXTERNAL"
CURSOR_MERGES = False

CLAIM_BOUNDARY = (
    "DIGITAL_PREPARATION of factory, RMA, support, supply-chain *fields*, "
    "and first-use software flow. DEV/TEST identities only. "
    "PRODUCTION_RELEASE_CLAIMED=false. No production keys, production CA, "
    "carrier eSIM, RFQ, purchase, or fab. Commercial warranty is EXTERNAL. "
    "Physical factory line, physical sanitize, and physical Ring/dock remain "
    "EXTERNAL/PHYSICAL. Cursor never merges."
)

EXTERNAL_ITEMS = (
    "production_keys",
    "production_ca_issuance",
    "hsm_key_ceremony",
    "carrier_esim_credentials",
    "rfq_purchase_fab",
    "physical_factory_line",
    "physical_media_sanitize",
    "commercial_warranty",
    "physical_ring_pairing",
    "physical_dock_discovery",
    "quoted_stock_price_lead_time_moq",
)
