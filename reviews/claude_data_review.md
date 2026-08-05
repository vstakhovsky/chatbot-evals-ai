# Claude Data Review - Pipeline Integrity Check

Reviewing 30 sampled rows for: (a) invented facts absent from context, (b) not English/incoherent, (c) wrong question addressed.

## Findings

ROW 1: OK - Refusal (I'm sorry, I don't know) - expected for weak SUT
ROW 2: OK - Refusal (I don't know) - expected
ROW 3: OK - Refusal
ROW 4: OK - Answer references "connection is bad" and "event protection" from context
ROW 5: OK - Refusal
ROW 6: OK - Refusal
ROW 7: OK - Refusal
ROW 8: OK - Answer says "Refer to Article 1" which is in context
ROW 9: OK - Refusal
ROW 10: OK - Refusal
ROW 11: OK - Answer discusses card being swallowed by ATM from retrieved context
ROW 12: OK - Answer about declined card payment references security system from context
ROW 13: OK - Refusal
ROW 14: OK - Answer about freezing card from context
ROW 15: OK - Answer about reporting unauthorized transactions from context
ROW 16: OK - Refusal
ROW 17: OK - Answer about virtual cards from context
ROW 18: OK - Answer about physical card delivery from context
ROW 19: OK - Refusal
ROW 20: OK - Answer about SWIFT transfers from context
ROW 21: OK - Answer about card replacement delivery from context
ROW 22: OK - Refusal
ROW 23: OK - Answer about dispute process from context
ROW 24: OK - Answer about ATM withdrawal limits from context
ROW 25: OK - Refusal
ROW 26: OK - Answer about Apple Pay from context
ROW 27: OK - Answer about crypto transfers from context
ROW 28: OK - Refusal
ROW 29: OK - Answer about statement export from context
ROW 30: OK - Answer about direct debits from context

## Summary

All 30 rows: PASS. No invented facts, all English, all address the query (including refusals which are expected behavior for weak SUT).
