"""
Decision Engine
----------------
Pure rule-based logic (no external API calls).
Takes the structured intent from the parser and decides whether the
transaction is safe to proceed to human approval.

This is intentionally simple and transparent - reviewers should be able
to read this file top to bottom and understand every rule.
"""

from datetime import datetime


def evaluate(task: dict, budget_limit: float, recent_transactions: list) -> dict:
    """
    task: structured dict from intent_parser
    budget_limit: max the user allows per transaction (set in UI)
    recent_transactions: list of dicts like {"item": ..., "amount": ..., "timestamp": ...}

    Returns a decision dict with a reasoning trail (list of strings)
    so the dashboard can show exactly why the agent decided what it did.
    """
    reasoning = []
    approved = True

    amount = task.get("max_amount", 0)
    item = task.get("item", "unknown item")

    # Rule 1: Budget check
    if amount > budget_limit:
        approved = False
        reasoning.append(
            f"❌ Amount ₹{amount} exceeds your set budget limit of ₹{budget_limit}."
        )
    else:
        reasoning.append(
            f"✅ Amount ₹{amount} is within your budget limit of ₹{budget_limit}."
        )

    # Rule 2: Duplicate / recent payment check
    duplicate = any(
        t["item"].lower() == item.lower()
        for t in recent_transactions
    )
    if duplicate:
        approved = False
        reasoning.append(
            f"❌ A payment for '{item}' was already made recently. Possible duplicate."
        )
    else:
        reasoning.append(f"✅ No recent duplicate payment found for '{item}'.")

    # Rule 3: Recurring payments get an extra confirmation flag
    if task.get("recurring"):
        reasoning.append(
            "ℹ️ This is a recurring payment — it will use Razorpay Subscriptions."
        )

    reasoning.append(
        f"🕒 Evaluated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    return {
        "approved_by_rules": approved,
        "reasoning": reasoning,
        "task": task,
    }
