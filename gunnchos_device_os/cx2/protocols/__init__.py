"""Local real protocol servers for Connect (SMTP/IMAP/CalDAV/CardDAV)."""

from .mail_servers import LocalMailStack
from .dav_server import LocalDavStack

__all__ = ["LocalMailStack", "LocalDavStack"]
