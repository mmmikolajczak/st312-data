from __future__ import annotations

import re


NUM_PATTERN = r"(?<![A-Za-z])\d+\.\d+|(?<![A-Za-z])\d+,\d+|(?<![A-Za-z])\d+/\d+|(?<![A-Za-z])\d+"
PATTERN4 = r"[A-Za-z]\d+"
PATTERN5 = r"\d+[A-Za-z]|\d+-[A-Za-z]"
FISCAL_YEAR = r"'\d+"
PHONE1 = r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
PHONE2 = r"\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*"
TIME1 = r"\d{1,2}:\d{2}"
TIME2 = r"\d{1,2}:\d{2}:\d{2}"


def get_partially_processed_text(line: str) -> str:
    covid = ["Covid-19", "Covid 19", "Covid'19"]
    months = ["January", "February", "March", "April", "May", "June", "July", "September", "October", "November", "December"]
    months_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Sep", "Sept", "Oct", "Nov", "Dec"]
    years = [f"20{year}" for year in range(10, 30)]
    text = line.strip()
    for match in covid:
        text = text.replace(match, "Covid").replace(match.lower(), "covid").replace(match.upper(), "COVID")
    while re.search(PHONE1, text):
        text = text.replace(re.search(PHONE1, text).group(0), "[PHONENUM]")
        text = text.replace("1-[PHONENUM]", "[PHONENUM]")
    while re.search(PHONE2, text):
        text = text.replace(re.search(PHONE2, text).group(0), "[PHONENUM]")
    while re.search(PATTERN4, text):
        text = text.replace(re.search(PATTERN4, text).group(0), "[TXT-NUM]")
    while re.search(PATTERN5, text):
        text = text.replace(re.search(PATTERN5, text).group(0), "[NUM-TXT]")
    while re.search(FISCAL_YEAR, text):
        text = text.replace(re.search(FISCAL_YEAR, text).group(0), "[YEAR]")
    for short_year in range(10, 30):
        text = text.replace(f"fy{short_year}", "financial year [YEAR]")
        text = text.replace(f"FY{short_year}", "financial year [YEAR]")
        text = text.replace(f"Fy{short_year}", "financial year [YEAR]")
    while re.search(TIME1, text):
        text = text.replace(re.search(TIME1, text).group(0), "[TIME] ")
    while re.search(TIME2, text):
        text = text.replace(re.search(TIME2, text).group(0), "[TIME] ")
    text = re.sub(r"\s\s+", " ", text)
    text = text.replace("[TIME] a.m.", "[TIME]").replace("[TIME] A.M.", "[TIME]").replace("[TIME] p.m.", "[TIME]").replace("[TIME] P.M.", "[TIME]")
    for match in re.findall(NUM_PATTERN, text):
        if match in years:
            text = text.replace(match, "[YEAR]")
        for month in months:
            text = text.replace(f"{month} {match}", "[DATE]").replace(f"{month.lower()} {match}", "[DATE]").replace(f"{month.upper()} {match}", "[DATE]")
        for month in months_short:
            text = text.replace(f"{month} {match}", "[DATE]").replace(f"{month.lower()} {match}", "[DATE]").replace(f"{month.upper()} {match}", "[DATE]")
        text = text.replace(f"slide {match}", "[SLIDE-NUM]").replace(f"Slide {match}", "[SLIDE-NUM]")
        text = text.replace(f"passcode {match}", "[PASSCODE]").replace(f"code {match}", "[PASSCODE]")
    text = " ".join(word if "[PASSCODE]" not in word else "[PASSCODE]" for word in text.split()).strip()
    return text


def extract_numeric_values(lines: list[str]) -> set[str]:
    values: set[str] = set()
    for line in lines:
        values.update(re.findall(NUM_PATTERN, get_partially_processed_text(line)))
    return values


def compute_num_prec(transcript_lines: list[str], reference_bullets: list[str], predicted_summary: str) -> float:
    predicted_lines = [line.strip() for line in predicted_summary.splitlines() if line.strip()]
    pred_vals = extract_numeric_values(predicted_lines)
    if not pred_vals:
        return 0.0
    source_vals = extract_numeric_values(transcript_lines)
    return len(pred_vals.intersection(source_vals)) / len(pred_vals)
