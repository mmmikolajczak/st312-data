import argparse
import json
from pathlib import Path

import nltk
from sklearn import metrics


def ensure_punkt():
    for res in ["tokenizers/punkt", "tokenizers/punkt_tab/english"]:
        try:
            nltk.data.find(res)
            return
        except LookupError:
            pass
    try:
        nltk.download("punkt", quiet=True)
    except Exception:
        pass
    try:
        nltk.download("punkt_tab", quiet=True)
    except Exception:
        pass


def build_token_index(text):
    ensure_punkt()
    tokens = nltk.word_tokenize(text)
    token_index = {}
    for position, token in enumerate(tokens):
        token_index.setdefault(token, []).append(position)
    return tokens, token_index


def _get_sequences(*args, value=None, path=None):
    if len(args) == 1:
        if value is not None:
            return [x for x in args[0] if x > value and (x < value + 3)]
        return [args[0]]
    result = []
    for x in args[0]:
        p = [x] if path is None else list(path + [x])
        if value is None or (x > value and (x < value + 3)):
            seqs = _get_sequences(*args[1:], value=x, path=p)
            if len(seqs) == 0 and (value is None or (x > value and (x < value + 3))):
                result.append([x])
            else:
                for s in seqs:
                    res = [x] + s if isinstance(s, list) else [x, s]
                    result.append(res)
    return result


def get_tokens_sequence(text, token_index):
    ensure_punkt()
    tokens = nltk.word_tokenize(text)
    positions = []
    for token in tokens:
        if token in token_index:
            positions.append(token_index[token])
            continue
        alt_token = "".join([token, "."])
        if alt_token in token_index:
            positions.append(token_index[alt_token])
            continue
    if len(positions) == 0:
        return positions
    seqs = _get_sequences(*positions)
    return max(seqs, key=len)


def encode_causal_tokens(text, cause, effect):
    words, wi = build_token_index(text)
    labels = ['-' for _ in range(len(words))]
    cause_seq = get_tokens_sequence(cause, wi)
    for position in cause_seq:
        labels[position] = 'C'
    effect_seq = get_tokens_sequence(effect, wi)
    for position in effect_seq:
        labels[position] = 'E'
    return list(zip(words, labels))


def _extract_json_object(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_prediction(pred_text: str):
    obj = _extract_json_object(pred_text)
    if obj is None:
        return None
    if set(obj.keys()) != {"cause", "effect"}:
        return None
    cause = obj["cause"]
    effect = obj["effect"]
    if not isinstance(cause, str) or not isinstance(effect, str):
        return None
    return {"cause": cause, "effect": effect}


def format_reward(pred_text: str) -> float:
    return 1.0 if parse_prediction(pred_text) is not None else 0.0


def official_single_example_scores(text: str, gold_cause: str, gold_effect: str, pred_cause: str, pred_effect: str):
    truth = [label for _, label in encode_causal_tokens(text, gold_cause, gold_effect)]
    pred = [label for _, label in encode_causal_tokens(text, pred_cause, pred_effect)]
    precision, recall, f1, _ = metrics.precision_recall_fscore_support(
        truth, pred, labels=['-', 'C', 'E'], average='weighted', zero_division=0
    )
    exact = 1.0 if all(x == y for x, y in zip(truth, pred)) else 0.0
    return precision, recall, f1, exact


def correctness_reward_industry(pred_text: str, text: str, gold_cause: str, gold_effect: str) -> float:
    pred = parse_prediction(pred_text)
    if pred is None:
        return 0.0
    _, _, f1, exact = official_single_example_scores(text, gold_cause, gold_effect, pred["cause"], pred["effect"])
    return 0.90 * f1 + 0.10 * exact


def total_reward(pred_text: str, text: str, gold_cause: str, gold_effect: str) -> float:
    return format_reward(pred_text) + correctness_reward_industry(pred_text, text, gold_cause, gold_effect)


def reward_breakdown(pred_text: str, text: str, gold_cause: str, gold_effect: str):
    pred = parse_prediction(pred_text)
    out = {
        "format_reward": format_reward(pred_text),
        "official_weighted_precision": 0.0,
        "official_weighted_recall": 0.0,
        "official_weighted_f1": 0.0,
        "official_exact_match": 0.0,
        "correctness_reward_industry": 0.0,
        "total_reward": 0.0,
    }
    if pred is not None:
        precision, recall, f1, exact = official_single_example_scores(text, gold_cause, gold_effect, pred["cause"], pred["effect"])
        out["official_weighted_precision"] = precision
        out["official_weighted_recall"] = recall
        out["official_weighted_f1"] = f1
        out["official_exact_match"] = exact
        out["correctness_reward_industry"] = 0.90 * f1 + 0.10 * exact
        out["total_reward"] = total_reward(pred_text, text, gold_cause, gold_effect)
    return out


def smoke_test():
    text = "Transat loss more than doubles as it works to complete Air Canada deal"
    gold_cause = "it works to complete Air Canada deal"
    gold_effect = "Transat loss more than doubles"

    cases = {
        "perfect": json.dumps({"cause": gold_cause, "effect": gold_effect}),
        "swapped": json.dumps({"cause": gold_effect, "effect": gold_cause}),
        "partial": json.dumps({"cause": "Air Canada deal", "effect": gold_effect}),
        "extra_key": json.dumps({"cause": gold_cause, "effect": gold_effect, "x": 1}),
        "not_json": "not json",
    }
    for name, txt in cases.items():
        pred = parse_prediction(txt)
        br = reward_breakdown(txt, text, gold_cause, gold_effect)
        print("=" * 88)
        print(f"Case: {name}")
        print(f"Parsed prediction: {pred}")
        for k, v in br.items():
            print(f"{k}={v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred-text", type=str, default=None)
    ap.add_argument("--text", type=str, default=None)
    ap.add_argument("--gold-cause", type=str, default=None)
    ap.add_argument("--gold-effect", type=str, default=None)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        smoke_test()
        return

    if None in [args.pred_text, args.text, args.gold_cause, args.gold_effect]:
        raise SystemExit("Provide --pred-text --text --gold-cause --gold-effect, or use --smoke-test")

    print(f"parsed_prediction={parse_prediction(args.pred_text)}")
    for k, v in reward_breakdown(args.pred_text, args.text, args.gold_cause, args.gold_effect).items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
