from __future__ import annotations

import re
import string
from functools import lru_cache
from typing import Any


SCALE_INVENTORY = ["", "thousand", "million", "billion", "percent"]
STRIPPED_CHARACTERS = string.punctuation + "".join(["‘", "’", "´", "`", "_"])
EXCLUDE_IN_NUM = "'\"\\$€£¥%(),[]"
EXCLUDE = set(string.punctuation)


def scale_to_num(scale: str) -> int | float:
    scale = scale.lower()
    if "hundred" in scale:
        return 100
    if "thousand" in scale:
        return 1000
    if "million" in scale:
        return 1000000
    if "billion" in scale:
        return 1000000000
    if "percent" in scale:
        return 0.01
    return 1


def _clean_num(text: str) -> str:
    return "".join(ch for ch in str(text) if ch not in EXCLUDE_IN_NUM)


def extract_one_num_from_str(text: str) -> int | float | None:
    cleaned = _clean_num(text)
    groups = re.findall(r"([+-]?\d+(\.\d+)?)|([+-]?\.\d+)", cleaned)
    if not groups:
        return None
    num = groups[0][0]
    if not num:
        return None
    return float(num) if "." in num else int(num)


def is_number(text: str) -> bool:
    try:
        words = " ".join(_clean_num(w) for w in str(text).split()).split()
        if not words:
            return False
        num = float(words[0])
        if num != num:
            return False
        if len(words) >= 2 and scale_to_num(words[1]) == 1:
            return False
        return True
    except ValueError:
        return False


def negative_num_handle(text: str) -> int:
    return -1 if re.findall(r"(\([\d.\s]+\))", text.strip()) else 1


def percent_num_handle(text: str) -> float:
    return 0.01 if re.findall(r"([\d.\s]+%)", text.strip()) else 1


def word_scale_handle(text: str) -> int | float:
    for match in re.finditer(r"([\d.]+\s?[a-zA-Z]+)", text):
        return scale_to_num(match.group(0).lower())
    return 1


def to_number(text: str) -> float | None:
    num = extract_one_num_from_str(text)
    if num is None:
        return None
    return round(num * word_scale_handle(text) * negative_num_handle(text) * percent_num_handle(text), 4)


def remove_articles(text: str) -> str:
    return re.sub(re.compile(r"\b(a|an|the)\b", re.UNICODE), " ", text)


def white_space_fix(text: str) -> str:
    return " ".join(text.split())


def remove_punc(text: str) -> str:
    if not is_number(text):
        return "".join(ch for ch in text if ch not in EXCLUDE)
    return text


def lower(text: str) -> str:
    return text.lower()


def tokenize(text: str) -> list[str]:
    return re.split(" ", text)


def normalize_number(text: str) -> str:
    if is_number(text):
        return str(to_number(text))
    return text


def normalize_answer(text: str) -> str:
    parts = [white_space_fix(remove_articles(normalize_number(remove_punc(lower(token))))) for token in tokenize(text)]
    parts = [part for part in parts if part.strip()]
    return " ".join(parts).strip()


def _answer_to_bags(answer: str | list[str] | tuple[str, ...]) -> tuple[list[str], list[set[str]]]:
    raw_spans = list(answer) if isinstance(answer, (list, tuple)) else [answer]
    normalized_spans: list[str] = []
    token_bags: list[set[str]] = []
    for raw_span in raw_spans:
        normalized_span = normalize_answer(str(raw_span))
        normalized_spans.append(normalized_span)
        token_bags.append(set(normalized_span.split()))
    return normalized_spans, token_bags


def _compute_f1(predicted_bag: set[str], gold_bag: set[str]) -> float:
    intersection = len(gold_bag.intersection(predicted_bag))
    precision = 1.0 if not predicted_bag else intersection / float(len(predicted_bag))
    recall = 1.0 if not gold_bag else intersection / float(len(gold_bag))
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _align_bags(predicted: list[set[str]], gold: list[set[str]]) -> list[float]:
    gold_len = len(gold)
    pred_len = len(predicted)
    if gold_len == 0 and pred_len == 0:
        return []
    if gold_len == 0 or pred_len == 0:
        return [0.0] * max(gold_len, pred_len)

    scores = [[_compute_f1(predicted[col], gold[row]) for col in range(pred_len)] for row in range(gold_len)]

    @lru_cache(maxsize=None)
    def best(row_idx: int, used_mask: int) -> tuple[float, tuple[tuple[int, int], ...]]:
        if row_idx >= gold_len:
            return 0.0, ()

        best_total, best_pairs = best(row_idx + 1, used_mask)
        for col_idx in range(pred_len):
            if used_mask & (1 << col_idx):
                continue
            child_total, child_pairs = best(row_idx + 1, used_mask | (1 << col_idx))
            total = scores[row_idx][col_idx] + child_total
            if total > best_total:
                best_total = total
                best_pairs = ((row_idx, col_idx),) + child_pairs
        return best_total, best_pairs

    _, pairs = best(0, 0)
    max_scores = [0.0] * max(gold_len, pred_len)
    for row_idx, col_idx in pairs:
        max_scores[row_idx] = max(max_scores[row_idx], scores[row_idx][col_idx])
    return max_scores


def get_metrics(predicted: str | list[str] | tuple[str, ...], gold: str | list[str] | tuple[str, ...]) -> tuple[float, float]:
    predicted_bags = _answer_to_bags(predicted)
    gold_bags = _answer_to_bags(gold)

    if set(predicted_bags[0]) == set(gold_bags[0]) and len(predicted_bags[0]) == len(gold_bags[0]):
        exact_match = 1.0
    else:
        exact_match = 0.0

    aligned = _align_bags(predicted_bags[1], gold_bags[1])
    f1 = round(sum(aligned) / len(aligned), 2) if aligned else 0.0
    return exact_match, f1


def extract_gold_answers(qa_annotation: dict[str, Any]) -> tuple[str, list[str], str]:
    answer_type = qa_annotation["answer_type"]
    if answer_type == "counting":
        answer_type = "count"
    scale = qa_annotation["scale"]
    answer_content = qa_annotation["answer"]
    gold_answers: list[str] = []
    if answer_type in ["multi-span", "span"]:
        if not isinstance(answer_content, list):
            raise ValueError(f"Expected list answer for {answer_type}, got {type(answer_content).__name__}")
        gold_answers = [str(x) for x in answer_content]
    elif answer_type == "arithmetic":
        gold_answers.append(str(answer_content))
    elif answer_type == "count":
        gold_answers.append(str(int(answer_content)))
    else:
        gold_answers.append(str(answer_content))
    return answer_type, gold_answers, scale


def metric_max_over_ground_truths(metric_fn, predictions: list[str], ground_truths: list[str]) -> tuple[float, float]:
    scores: list[tuple[float, float]] = []
    for pred in predictions:
        for truth in ground_truths:
            scores.append(metric_fn(pred, truth))
    if not scores:
        return 0.0, 0.0
    return max(scores, key=lambda item: (item[0], item[1]))


def get_answer_str(answers: list[Any], scale: str) -> list[str]:
    sorted_ans = sorted(answers, key=lambda item: str(item))
    normalized_answers: list[str] = []
    for ans in sorted_ans:
        ans_str = str(ans)
        if is_number(ans_str):
            ans_num = to_number(ans_str)
            if ans_num is None:
                if scale:
                    ans_str = ans_str + " " + str(scale)
            else:
                if "%" in ans_str:
                    ans_str = "%.4f" % ans_num
                else:
                    ans_str = "%.4f" % (round(ans_num, 2) * scale_to_num(scale))
        else:
            if scale:
                ans_str = ans_str + " " + str(scale)
        normalized_answers.append(ans_str)
    return [" ".join(normalized_answers)]


def add_percent_pred(prediction_strings: list[str], pred_scale: str, pred: list[Any]) -> list[str]:
    if len(pred) > 1:
        return prediction_strings
    pred_str = str(pred[0])
    if pred_str is None:
        return prediction_strings
    if not pred_scale and "%" not in pred_str and is_number(pred_str):
        pred_num = to_number(pred_str)
        if pred_num is not None:
            prediction_strings.append("%.4f" % pred_num)
    return prediction_strings


def processed_row_to_official_ground_truth(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "uid": row["example_id"],
        "answer": row["gold_answer"],
        "answer_type": row["gold_answer_type_raw"],
        "answer_from": row["gold_answer_from"],
        "scale": row["gold_scale"],
    }


def score_prediction(ground_truth: dict[str, Any], prediction: Any, pred_scale: str = "") -> dict[str, float]:
    scale_match = 0.0
    if pred_scale == ground_truth["scale"]:
        scale_match = 1.0

    if prediction in [None, "", []]:
        return {"exact_match": 0.0, "f1": 0.0, "scale_score": scale_match}

    gold_type, gold_answer, gold_scale = extract_gold_answers(ground_truth)
    if not gold_answer:
        return {"exact_match": 0.0, "f1": 0.0, "scale_score": scale_match}

    prediction_values = prediction if isinstance(prediction, list) else [prediction]
    prediction_strings = get_answer_str(prediction_values, pred_scale)
    prediction_strings = add_percent_pred(prediction_strings, pred_scale, prediction_values)
    ground_truth_strings = get_answer_str(gold_answer, gold_scale)
    exact_match, f1 = metric_max_over_ground_truths(get_metrics, prediction_strings, ground_truth_strings)
    if gold_type in ["arithmetic", "count"]:
        f1 = exact_match
    return {"exact_match": exact_match, "f1": f1, "scale_score": scale_match}


class OfficialTATQAMetric:
    def __init__(self) -> None:
        self._count = 0
        self._total_em = 0.0
        self._total_f1 = 0.0
        self._total_scale = 0.0
        self._details: list[dict[str, Any]] = []

    def add(self, ground_truth: dict[str, Any], prediction: Any, pred_scale: str = "") -> dict[str, float]:
        score = score_prediction(ground_truth, prediction, pred_scale)
        self._count += 1
        self._total_em += score["exact_match"]
        self._total_f1 += score["f1"]
        self._total_scale += score["scale_score"]
        self._details.append(
            {
                "uid": ground_truth.get("uid"),
                "answer_type": ground_truth.get("answer_type"),
                "answer_from": ground_truth.get("answer_from"),
                "gold_scale": ground_truth.get("scale"),
                "pred_scale": pred_scale,
                "exact_match": score["exact_match"],
                "f1": score["f1"],
                "scale_score": score["scale_score"],
            }
        )
        return score

    def get_overall_metric(self) -> dict[str, float]:
        if self._count == 0:
            return {"exact_match": 0.0, "f1": 0.0, "scale_score": 0.0}
        return {
            "exact_match": self._total_em / self._count,
            "f1": self._total_f1 / self._count,
            "scale_score": self._total_scale / self._count,
        }

    def get_details(self) -> list[dict[str, Any]]:
        return list(self._details)


def to_official_prediction_dict(predictions: dict[str, dict[str, Any] | None]) -> dict[str, list[Any]]:
    formatted: dict[str, list[Any]] = {}
    for example_id, prediction in predictions.items():
        if prediction is None:
            continue
        formatted[example_id] = [prediction["answer"], prediction["scale"]]
    return formatted
