"""
Hard validators for the Study Guide Generation backend.

Hard validators block document assembly. A section that fails is retried once.
If the retry also fails, the section is assembled as best_effort.
"""
