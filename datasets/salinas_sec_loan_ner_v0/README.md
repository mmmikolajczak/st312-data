# Salinas SEC Loan Agreements NER Dataset (v0)

Dataset module for token-level named entity recognition on the financial loan-agreement corpus of Salinas Alvarado, Verspoor, and Baldwin (2015).

## Dataset ID

`salinas_sec_loan_ner_v0`

## Canonical provenance

- Paper: Salinas Alvarado, Verspoor, and Baldwin (2015)
- ACL Anthology PDF: `https://aclanthology.org/U15-1010.pdf`
- Original release URL: `http://people.eng.unimelb.edu.au/tbaldwin/resources/finance-sec/`
- Raw mirror used for retrieval: `tner/fin`

## Canonical processed files

- `data/salinas_sec_loan_ner/processed/salinas_sec_loan_ner_all_clean.jsonl`
- `data/salinas_sec_loan_ner/processed/salinas_sec_loan_ner_train.jsonl`
- `data/salinas_sec_loan_ner/processed/salinas_sec_loan_ner_test.jsonl`

## Label handling

- Original CoNLL-style NER tags are preserved in `label.original_tags`
- Derived BIO2 tags for training/eval are stored in `label.tags`
- Entity types retained: `PER`, `LOC`, `ORG`, `MISC`
- Original token/POS/chunk columns are preserved in the cleaned records

## Split policy

Original author split:
- `FIN5.txt` -> train
- `FIN3.txt` -> test

Any internal dev split, if later needed, should be derived from `FIN5` only.

## Corpus-specific note

The paper states that all instances of the tokens `lender` and `borrower` were automatically tagged as `PER`. This is preserved as corpus provenance and not overridden locally.
