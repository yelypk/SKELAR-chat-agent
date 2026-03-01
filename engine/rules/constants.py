from __future__ import annotations

ESCALATION_RULE_SIM_THRESHOLD = 0.12
FORBIDDEN_ACTION_SIM_THRESHOLD = 0.22
REQUIRED_QUESTION_SIM_THRESHOLD = 0.15
RESOLUTION_EMBEDDING_THRESHOLD = 0.86
RESOLUTION_LEXICAL_THRESHOLD = 0.22
DEADLOCK_SIMILARITY_CAP = 0.85

HIGH_RISK_ESCALATION_MARKERS = (
    "fraud",
    "compliance",
    "security",
    "legal",
    "chargeback",
    "supervisor",
    "manager",
)

RESOLUTION_BLOCKERS = (
    "still",
    "not working",
    "didn't help",
    "same issue",
    "not fixed",
    "doesn't work",
)

RESOLUTION_CONFIRMATIONS = (
    "thanks",
    "thank you",
    "that worked",
    "works now",
    "fixed",
    "resolved",
    "got it",
    "perfect",
    "all good",
)

SUPPORT_CLOSING_OFFER_MARKERS = (
    "anything else",
    "else i can help",
    "can i help",
    "other issue",
)

SUPPORT_CLOSING_GOODBYE_MARKERS = (
    "goodbye",
    "have a nice day",
    "have a great day",
    "take care",
    "bye",
)

CUSTOMER_COMMITMENT_MARKERS = ("i'll", "i will", "that works", "thanks", "okay")
CUSTOMER_LATER_PROGRESS_MARKERS = ("upload", "later", "once", "when", "reply here")
CUSTOMER_COMMITMENT_SHORT_MARKERS = ("i'll", "i will", "thanks", "that works")

RUDE_MARKERS = frozenset(
    {
        "stupid",
        "dumb",
        "your fault",
        "nonsense",
        "can't you read",
        "stop wasting",
    }
)
