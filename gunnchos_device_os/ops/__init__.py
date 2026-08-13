"""Factory / RMA / support digital operational model — DEV/TEST only.

DIGITAL_PREPARATION of software workflows. Physical factory, RFQ, purchase,
fab, production keys, production CA, carrier eSIM, commercial warranty, and
physical Ring/dock pairing remain EXTERNAL.
"""

from gunnchos_device_os.ops.claim import (
    CLAIM_BOUNDARY,
    COMMERCIAL_WARRANTY,
    PRODUCTION_RELEASE_CLAIMED,
)

__all__ = [
    "CLAIM_BOUNDARY",
    "COMMERCIAL_WARRANTY",
    "PRODUCTION_RELEASE_CLAIMED",
]
