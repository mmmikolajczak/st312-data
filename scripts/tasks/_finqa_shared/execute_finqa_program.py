from __future__ import annotations

from sympy import simplify

from normalize_finqa_answer import normalize_finqa_answer


OFFICIAL_OPERATION_NAMES = [
    "add",
    "subtract",
    "multiply",
    "divide",
    "exp",
    "greater",
    "table_max",
    "table_min",
    "table_sum",
    "table_average",
]
CANONICAL_OPERATION_TOKENS = [f"{op}(" for op in OFFICIAL_OPERATION_NAMES]
END_TOKEN = "EOF"
CLOSE_TOKEN = ")"
REFERENCE_PREFIX = "#"


def str_to_num(text: str):
    text = text.replace(",", "")
    try:
        num = float(text)
    except ValueError:
        if "%" in text:
            text = text.replace("%", "")
            try:
                num = float(text)
                num = num / 100.0
            except ValueError:
                num = "n/a"
        elif "const" in text:
            text = text.replace("const_", "")
            if text == "m1":
                text = "-1"
            num = float(text)
        else:
            num = "n/a"
    return num


def process_row(row_in: list[str]):
    row_out = []
    invalid_flag = 0

    for num in row_in:
        num = num.replace("$", "").strip()
        num = num.split("(")[0].strip()
        num = str_to_num(num)

        if num == "n/a":
            invalid_flag = 1
            break

        row_out.append(num)

    if invalid_flag:
        return "n/a"

    return row_out


def eval_program(program: list[str], table: list[list[str]]):
    invalid_flag = 0
    this_res = "n/a"

    try:
        program = program[:-1]
        for ind, token in enumerate(program):
            if ind % 4 == 0:
                if token.strip("(") not in OFFICIAL_OPERATION_NAMES:
                    return 1, "n/a"
            if (ind + 1) % 4 == 0 and token != CLOSE_TOKEN:
                return 1, "n/a"

        program = "|".join(program)
        steps = program.split(")")[:-1]

        res_dict = {}

        for ind, step in enumerate(steps):
            step = step.strip()

            if len(step.split("(")) > 2:
                invalid_flag = 1
                break

            op = step.split("(")[0].strip("|").strip()
            args = step.split("(")[1].strip("|").strip()
            arg1 = args.split("|")[0].strip()
            arg2 = args.split("|")[1].strip()

            if op in {"add", "subtract", "multiply", "divide", "exp", "greater"}:
                if REFERENCE_PREFIX in arg1:
                    arg1 = res_dict[int(arg1.replace(REFERENCE_PREFIX, ""))]
                else:
                    arg1 = str_to_num(arg1)
                    if arg1 == "n/a":
                        invalid_flag = 1
                        break

                if REFERENCE_PREFIX in arg2:
                    arg2 = res_dict[int(arg2.replace(REFERENCE_PREFIX, ""))]
                else:
                    arg2 = str_to_num(arg2)
                    if arg2 == "n/a":
                        invalid_flag = 1
                        break

                if op == "add":
                    this_res = arg1 + arg2
                elif op == "subtract":
                    this_res = arg1 - arg2
                elif op == "multiply":
                    this_res = arg1 * arg2
                elif op == "divide":
                    this_res = arg1 / arg2
                elif op == "exp":
                    this_res = arg1**arg2
                elif op == "greater":
                    this_res = "yes" if arg1 > arg2 else "no"

                res_dict[ind] = this_res

            elif "table" in op:
                table_dict = {}
                for row in table:
                    table_dict[row[0]] = row[1:]

                if REFERENCE_PREFIX in arg1:
                    arg1 = res_dict[int(arg1.replace(REFERENCE_PREFIX, ""))]
                    num_row = arg1
                else:
                    if arg1 not in table_dict:
                        invalid_flag = 1
                        break

                    cal_row = table_dict[arg1]
                    num_row = process_row(cal_row)

                if num_row == "n/a":
                    invalid_flag = 1
                    break

                if op == "table_max":
                    this_res = max(num_row)
                elif op == "table_min":
                    this_res = min(num_row)
                elif op == "table_sum":
                    this_res = sum(num_row)
                elif op == "table_average":
                    this_res = sum(num_row) / len(num_row)

                res_dict[ind] = this_res

        if this_res not in {"yes", "no", "n/a"}:
            this_res = round(this_res, 5)

    except Exception:
        invalid_flag = 1

    return invalid_flag, this_res


def equal_program(program1: list[str], program2: list[str]) -> bool:
    sym_map = {}

    program1 = program1[:-1]
    program1 = "|".join(program1)
    steps = program1.split(")")[:-1]

    sym_ind = 0
    step_dict_1 = {}

    for ind, step in enumerate(steps):
        step = step.strip()
        assert len(step.split("(")) <= 2

        op = step.split("(")[0].strip("|").strip()
        args = step.split("(")[1].strip("|").strip()

        arg1 = args.split("|")[0].strip()
        arg2 = args.split("|")[1].strip()

        step_dict_1[ind] = step

        if "table" in op:
            if step not in sym_map:
                sym_map[step] = "a" + str(sym_ind)
                sym_ind += 1
        else:
            if REFERENCE_PREFIX not in arg1 and arg1 not in sym_map:
                sym_map[arg1] = "a" + str(sym_ind)
                sym_ind += 1
            if REFERENCE_PREFIX not in arg2 and arg2 not in sym_map:
                sym_map[arg2] = "a" + str(sym_ind)
                sym_ind += 1

    step_dict_2 = {}
    try:
        program2 = program2[:-1]
        for ind, token in enumerate(program2):
            if ind % 4 == 0 and token.strip("(") not in OFFICIAL_OPERATION_NAMES:
                return False
            if (ind + 1) % 4 == 0 and token != CLOSE_TOKEN:
                return False

        program2 = "|".join(program2)
        steps = program2.split(")")[:-1]

        for ind, step in enumerate(steps):
            step = step.strip()
            if len(step.split("(")) > 2:
                return False

            op = step.split("(")[0].strip("|").strip()
            args = step.split("(")[1].strip("|").strip()
            arg1 = args.split("|")[0].strip()
            arg2 = args.split("|")[1].strip()

            step_dict_2[ind] = step

            if "table" in op:
                if step not in sym_map:
                    return False
            else:
                if REFERENCE_PREFIX not in arg1:
                    if arg1 not in sym_map:
                        return False
                elif int(arg1.strip(REFERENCE_PREFIX)) >= ind:
                    return False

                if REFERENCE_PREFIX not in arg2:
                    if arg2 not in sym_map:
                        return False
                elif int(arg2.strip(REFERENCE_PREFIX)) >= ind:
                    return False
    except Exception:
        return False

    def symbol_recur(step: str, step_dict: dict[int, str]) -> str:
        step = step.strip()
        op = step.split("(")[0].strip("|").strip()
        args = step.split("(")[1].strip("|").strip()

        arg1 = args.split("|")[0].strip()
        arg2 = args.split("|")[1].strip()

        if "table" in op:
            return sym_map[step]

        if REFERENCE_PREFIX in arg1:
            arg1_part = symbol_recur(step_dict[int(arg1.replace(REFERENCE_PREFIX, ""))], step_dict)
        else:
            arg1_part = sym_map[arg1]

        if REFERENCE_PREFIX in arg2:
            arg2_part = symbol_recur(step_dict[int(arg2.replace(REFERENCE_PREFIX, ""))], step_dict)
        else:
            arg2_part = sym_map[arg2]

        if op == "add":
            return "( " + arg1_part + " + " + arg2_part + " )"
        if op == "subtract":
            return "( " + arg1_part + " - " + arg2_part + " )"
        if op == "multiply":
            return "( " + arg1_part + " * " + arg2_part + " )"
        if op == "divide":
            return "( " + arg1_part + " / " + arg2_part + " )"
        if op == "exp":
            return "( " + arg1_part + " ** " + arg2_part + " )"
        if op == "greater":
            return "( " + arg1_part + " > " + arg2_part + " )"
        raise ValueError(f"Unsupported op {op}")

    steps = program1.split(")")[:-1]
    sym_prog1 = simplify(symbol_recur(steps[-1], step_dict_1), evaluate=False)

    try:
        steps = program2.split(")")[:-1]
        sym_prog2 = simplify(symbol_recur(steps[-1], step_dict_2), evaluate=False)
    except Exception:
        return False

    return sym_prog1 == sym_prog2


def program_exact_match(gold_program: list[str], predicted_program: list[str]) -> bool:
    return gold_program == predicted_program


def execution_matches_gold(program: list[str], table: list[list[str]], gold_answer: object) -> tuple[bool, int, object]:
    invalid_flag, result = eval_program(program, table)
    normalized_result = normalize_finqa_answer(result)
    normalized_gold = normalize_finqa_answer(gold_answer)
    return invalid_flag == 0 and normalized_result == normalized_gold, invalid_flag, result
