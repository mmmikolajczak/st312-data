from __future__ import annotations

from collections import Counter

from multilabel_metrics import precision_recall_f1, safe_div


INVALID_OR_MISSING = "INVALID_OR_MISSING"


def compute_multiclass_metrics(
    gold_labels: list[str],
    pred_labels: list[str | None],
    label_inventory: list[str],
) -> dict:
    per_class = {}
    macro_f1s = []
    weighted_f1_sum = 0.0
    confusion = Counter()
    correct = 0

    for gold, pred in zip(gold_labels, pred_labels):
        normalized_pred = pred if pred is not None else INVALID_OR_MISSING
        confusion[(gold, normalized_pred)] += 1
        if pred == gold:
            correct += 1

    for label in label_inventory:
        tp = fp = fn = tn = 0
        for gold, pred in zip(gold_labels, pred_labels):
            pred_is_label = pred == label
            gold_is_label = gold == label
            if gold_is_label and pred_is_label:
                tp += 1
            elif not gold_is_label and pred_is_label:
                fp += 1
            elif gold_is_label and not pred_is_label:
                fn += 1
            else:
                tn += 1
        precision, recall, f1 = precision_recall_f1(tp, fp, fn)
        support = tp + fn
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "support": support,
        }
        macro_f1s.append(f1)
        weighted_f1_sum += f1 * support

    total_examples = len(gold_labels)
    total_support = sum(per_class[label]["support"] for label in label_inventory)
    return {
        "accuracy": safe_div(correct, total_examples),
        "macro_f1": safe_div(sum(macro_f1s), len(macro_f1s)),
        "weighted_f1": safe_div(weighted_f1_sum, total_support),
        "per_class": per_class,
        "confusion_counts": {
            f"{gold} -> {pred}": count
            for (gold, pred), count in sorted(confusion.items())
        },
    }
