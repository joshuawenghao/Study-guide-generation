"""
Hard validators.

Each validator function accepts typed inputs and returns a list of failure
messages. An empty list means the validator passed.
"""

from backend.validators.hard.vocab_presence import check_vocab_presence
from backend.validators.hard.self_assess_targets import check_self_assess_targets
from backend.validators.hard.answer_key_quotes import check_answer_key_quotes
from backend.validators.hard.passage_domain_diff import check_passage_domain_diff

__all__ = [
    "check_vocab_presence",
    "check_self_assess_targets",
    "check_answer_key_quotes",
    "check_passage_domain_diff",
]
