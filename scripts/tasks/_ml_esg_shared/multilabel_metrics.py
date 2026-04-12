from __future__ import annotations


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    if tp == 0 and fp == 0 and fn == 0:
        return 1.0, 1.0, 1.0
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def label_set_f1(pred_labels: list[str], gold_labels: list[str]) -> float:
    pred_set = set(pred_labels)
    gold_set = set(gold_labels)
    if not pred_set and not gold_set:
        return 1.0
    intersection = len(pred_set & gold_set)
    return safe_div(2 * intersection, len(pred_set) + len(gold_set))


def compute_multilabel_metrics(
    gold_label_lists: list[list[str]],
    pred_label_lists: list[list[str]],
    label_inventory: list[str],
) -> dict:
    per_label = {}
    macro_f1s = []
    micro_tp = micro_fp = micro_fn = 0
    exact_matches = 0
    example_f1s = []
    predicted_label_count_sum = 0
    gold_label_count_sum = 0

    for label in label_inventory:
        tp = fp = fn = tn = 0
        for gold_labels, pred_labels in zip(gold_label_lists, pred_label_lists):
            gold_has = label in gold_labels
            pred_has = label in pred_labels
            if gold_has and pred_has:
                tp += 1
            elif pred_has and not gold_has:
                fp += 1
            elif gold_has and not pred_has:
                fn += 1
            else:
                tn += 1
        precision, recall, f1 = precision_recall_f1(tp, fp, fn)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }
        macro_f1s.append(f1)
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn

    for gold_labels, pred_labels in zip(gold_label_lists, pred_label_lists):
        exact_matches += int(set(gold_labels) == set(pred_labels))
        example_f1s.append(label_set_f1(pred_labels, gold_labels))
        predicted_label_count_sum += len(pred_labels)
        gold_label_count_sum += len(gold_labels)

    micro_precision, micro_recall, micro_f1 = precision_recall_f1(micro_tp, micro_fp, micro_fn)

    total_examples = len(gold_label_lists)
    return {
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_f1,
        "macro_f1": sum(macro_f1s) / len(macro_f1s),
        "example_f1_mean": sum(example_f1s) / len(example_f1s),
        "subset_accuracy": safe_div(exact_matches, total_examples),
        "avg_predicted_label_count": safe_div(predicted_label_count_sum, total_examples),
        "avg_gold_label_count": safe_div(gold_label_count_sum, total_examples),
        "per_label_metrics": per_label,
    }
