"""
Razorpay Integration
----------------------
Creates a real TEST-mode Razorpay Payment Link (or Order) once the
human has approved the transaction.

Docs: https://razorpay.com/docs/api/payments/payment-links/
"""

import razorpay


def get_client(key_id: str, key_secret: str) -> razorpay.Client:
    client = razorpay.Client(auth=(key_id, key_secret))
    return client


def create_payment_link(client: razorpay.Client, task: dict, customer_name: str, customer_email: str) -> dict:
    """
    Creates a Razorpay Payment Link in TEST mode for the approved task.
    Amount must be sent in paise (multiply INR by 100).
    """
    amount_paise = int(task["max_amount"] * 100)

    payload = {
        "amount": amount_paise,
        "currency": task.get("currency", "INR"),
        "accept_partial": False,
        "description": f"AutoCart: {task.get('item', 'Item')}",
        "customer": {
            "name": customer_name,
            "email": customer_email,
        },
        "notify": {
            "sms": False,
            "email": True,
        },
        "reminder_enable": False,
    }

    link = client.payment_link.create(payload)
    return link
