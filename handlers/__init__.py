# handlers/__init__.py

# Для /start
from .start import start_handler

# Для согласия (ConversationHandler)
from .consent import (
    consent_start,
    consent_full_name,
    full_name_received,
    phone_received,
    email_received,
    consent_confirm,
    consent_restart,
    cancel,
    FULL_NAME, PHONE, EMAIL, CONFIRM
)
from .admin import leads_handler, count_handler

__all__ = [
    "start_handler",
    "consent_start", "consent_full_name", "full_name_received",
    "phone_received", "email_received", "consent_confirm",
    "consent_restart", "cancel",
    "FULL_NAME", "PHONE", "EMAIL", "CONFIRM", "leads_handler",  "count_handler"
]

