# handlers/__init__.py

# Для /start
from .start import start_handler, handle_main_menu
from .about import about_handler
from .reviews import reviews_handler
from .product import product_handler
from .booking import booking_handler
# from .consent import consent_handler, start_form_handler # Влада проверить
from .guide import (
    guide_handler, 
    check_subscription_handler, 
    download_guide_handler,
    show_guides_list
)

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

from .admin import (
    albina_handler,
    admin_ask_leads_callback,
    admin_count_now_callback,
    admin_export_csv_callback,
    admin_upload_guide_callback,   # ← новое
    process_leads_count,
    receive_guide_file,            # ← новое
    count_handler,
    cancel as admin_cancel,        # ← чтобы не конфликтовало с consent.cancel
    ASK_LEADS_COUNT,
    AWAIT_GUIDE_FILE               # ← новое
)

__all__ = [
    "start_handler",
    "consent_start", "consent_full_name", "full_name_received",
    "phone_received", "email_received", "consent_confirm",
    "consent_restart", "cancel",
    "FULL_NAME", "PHONE", "EMAIL", "CONFIRM", "leads_handler",  "count_handler" ,  
    'handle_main_menu',
    'about_handler',
    'reviews_handler',
    'product_handler',
    'booking_handler',
    'consent_handler',
    'start_form_handler',
    'guide_handler',
    'check_subscription_handler',
    'albina_handler', 'admin_ask_leads_callback',
    'admin_count_now_callback', 'process_leads_count',
    'ASK_LEADS_COUNT', 'admin_export_csv_callback',
    'admin_upload_guide_callback', 'receive_guide_file',
    'admin_cancel'
]

