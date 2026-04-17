from __future__ import annotations


def render_user_prompt(row: dict) -> str:
    return (
        "The following applicant attributes come from the UCI Statlog German Credit dataset.\n"
        "Use them as a historical credit-scoring benchmark input, not as a deployment recommendation.\n\n"
        f"Applicant features:\n{row['feature_text_decoded']}\n\n"
        "Return JSON only in this form:\n"
        '{"label":"good"}'
    )

