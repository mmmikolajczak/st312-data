# FinRED Official Release Dataset (v0)

Dataset module for the official author release of FinRED.

## Dataset ID

`finred_official_v0`

## Canonical provenance

- Official repo: `https://github.com/soummyaah/FinRED`
- Official data folder: `https://drive.google.com/drive/folders/1-k5H79NkqzLkkF4KcndqxAPojnBbmqa4?usp=sharing`
- Paper: `https://arxiv.org/pdf/2306.03736`

## Key notes

- Preserve the author-provided `train/dev/test` split
- Treat train/dev as weakly supervised / distantly supervised
- Keep the manually cleaned test split for evaluation
- Released raw format is aligned across `.sent`, `.tup`, `.pointer`, and `.txt`
- Relation inventory contains 29 relations
- The released-file counts are `5700 / 1007 / 1068`, summing to `7775`, which matches the paper's total size even though one reported train count in the paper differs by one
