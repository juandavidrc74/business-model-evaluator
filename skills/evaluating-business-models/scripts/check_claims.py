"""Anti-fabrication check (RS-FAB-01/04, RT-BMK-03): every number in the Markdown report must exist
in the EVIDENCE sections of evaluation.json (ledger values and quotes, script outputs), and every
cited benchmark id must carry a date.

Hardening after the independent audit (REV-001):
- Only evidence sections count as support. Free text written by the model (proposal_title,
  neutral_restatement, strongest_case_against, claim descriptions, runs) and above all
  injection_findings (attacker text) are NOT accepted as support.
- Inside evidence sections, numbers in strings are read only from whitelisted keys produced by
  documents or scripts (quote, value, value_text, reason, reversal_condition, condition, detail, cite).
- Magnitude suffixes are normalised: '2,3 M', '2,3 millones', '1,2 MM', '850 k', '3 mil', '1,5 bn'.
- Written Spanish dates are ignored ('10 de noviembre de 2026', 'nov-2026', 'en 2026').
- Numbers written in words with a magnitude or currency ('cincuenta mil dolares') are flagged:
  the report must use numerals so they can be checked.

Spanish number formats are normalised: '1.500' (thousands dot), '1,5' (decimal comma), '12 %'.
Ambiguous forms are expanded into every plausible reading and pass if any reading matches.

Usage: python check_claims.py report.md evaluation.json      -> exit 1 on any unsupported number
"""
from __future__ import annotations

import json
import re
import sys

from _common import load_json

EVIDENCE_SECTIONS = {"ledger", "gates", "modules", "dimensions", "ue_metrics", "projection", "stress_table", "market",
                     "competitors", "forecasts", "conditions", "reversal_conditions", "p0_list", "extracted_figures",
                     "tests", "flags", "alerts", "lines", "web_calls", "tornado", "monte_carlo", "scenarios",
                     "ai_native", "benchmarks"}
STRING_KEYS = {"quote", "value", "value_text", "reason", "reversal_condition", "condition", "detail", "cite"}
MONTHS = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
ID_RE = re.compile(r"\b(?:SVC|PRD|FIN|AI|MKT|DD|VAL|GEO|P1)-\d{3}\b")
SKIP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"                      # ISO dates
    r"|\b\d{1,2}\s+de\s+" + MONTHS + r"(?:\s+(?:de|del)\s+\d{4})?\b"     # 10 de noviembre (de 2026)
    r"|\b" + MONTHS + r"\s+(?:de|del)\s+\d{4}\b"                      # noviembre de 2026
    r"|\b" + r"(?:ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|may(?:o)?|jun(?:io)?|jul(?:io)?|ago(?:sto)?|"
    r"sep(?:tiembre)?|set(?:iembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?)\.?[-\s](?:19|20)\d{2}\b"  # nov-2026
    r"|\b(?:en|del|desde|hasta|año|anio|ejercicio|FY|cohorte)\s?(?:19|20)\d{2}\b"  # en 2026, FY2026
    r"|\b(?:SVC|PRD|FIN|AI|MKT|DD|VAL|GEO|P1|GAP|RF|RT|RS|RQ)-[A-Z]*-?\d+\b"   # ids
    r"|\b(?:M|G|T|H|R|D|UE-|FM-|SA-|AI_T)\d+[a-z]?(?:\.\d+)?\b"             # module/gate/rule ids
    r"|\bG2b\b|\bp(?:50|90|95|99|10)\b|\bP(?:0|1|2)\b|\bL\d+\b"
    r"|\bpass\^\d+\b|\bx\s?\d+(?:[.,]\d+)?\b|\b\d+(?:[.,]\d+)?x\b|\b\d+/\d+\b(?= ejecuciones)"
    r"|^\s*\d+\.\s"                                # numbered list markers
    r"|\[\d+\]",
    re.M | re.I)
NUM_RE = re.compile(r"(?<![\w.,])[-−]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w.,])[-−]?\d+(?:[.,]\d+)?")
SUFFIX_RE = re.compile(r"\s?(mil\s+millones|millones|mill\.?|MM|M|bn|billones|k|K|mil)\b")
SUFFIX_MULT = {"mil millones": 1e9, "millones": 1e6, "mill": 1e6, "mill.": 1e6, "MM": 1e6, "M": 1e6, "bn": 1e9,
               "billones": 1e12, "k": 1e3, "K": 1e3, "mil": 1e3}
WORD_NUM_RE = re.compile(
    r"\b(?:un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|quince|veinte|treinta|cuarenta|"
    r"cincuenta|sesenta|setenta|ochenta|noventa|cien|ciento|doscientos|trescientos|quinientos|mil)\b"
    r"(?:\s+\w+){0,2}?\s+(?:mil|millones|millón|millon|dólares|dolares|pesos|euros|USD|COP|EUR|por\s+ciento)\b", re.I)
DATE_NEAR_RE = re.compile(r"\b(?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?\b", re.I)   # any year or ISO date on the line


def readings(token: str) -> set[float]:
    t = token.replace("−", "-")
    out = set()
    if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):
        out.add(float(t.replace(".", "").replace(",", ".")))
        if t.count(".") == 1 and "," not in t:
            out.add(float(t))                      # could be an English decimal (1.500 -> 1.5)
    elif "," in t:
        out.add(float(t.replace(",", ".")))
    else:
        out.add(float(t))
    return out


def _numbers_in_text(text: str, acc: set[float]):
    clean = SKIP_RE.sub(" ", text)
    for m in NUM_RE.finditer(clean):
        rs = readings(m.group(0))
        acc |= rs
        s = SUFFIX_RE.match(clean, m.end())
        if s:
            mult = SUFFIX_MULT.get(s.group(1), SUFFIX_MULT.get(s.group(1).lower(), 1))
            acc |= {r * mult for r in rs}


def collect_numbers(obj, acc: set[float], key: str | None = None):
    """Collect numbers from an evidence subtree: all numeric values, and strings only under STRING_KEYS."""
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        acc.add(float(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k == "claim":            # model-written description, not evidence
                continue
            collect_numbers(v, acc, k)
    elif isinstance(obj, list):
        for v in obj:
            collect_numbers(v, acc, key)
    elif isinstance(obj, str) and key in STRING_KEYS:
        _numbers_in_text(obj, acc)


def evidence_pool(evaluation: dict) -> set[float]:
    pool: set[float] = set()
    for section, content in (evaluation or {}).items():
        if section in EVIDENCE_SECTIONS:
            collect_numbers(content, pool, section)
    return pool


def supported(x: float, pool: set[float]) -> bool:
    for v in pool:
        for cand in (v, v * 100, v / 100):
            if cand == 0 and x == 0:
                return True
            if cand != 0:
                if abs(x - cand) <= max(0.005 * abs(cand), 1e-9):     # rounding in the narrative
                    return True
                # displayed with fewer decimals or two significant figures
                for nd in range(0, 4):
                    if round(cand, nd) == x:
                        return True
                mag = 10 ** (len(str(int(abs(cand)))) - 2) if abs(cand) >= 100 else None
                if mag and round(cand / mag) * mag == x:
                    return True
    return False


def check(report_text: str, evaluation: dict) -> dict:
    pool = evidence_pool(evaluation)
    unsupported, missing_dates, worded = [], [], []
    for ln_no, line in enumerate(report_text.splitlines(), start=1):
        clean = SKIP_RE.sub(" ", line)
        for m in NUM_RE.finditer(clean):
            tok = m.group(0)
            rs = readings(tok)
            s = SUFFIX_RE.match(clean, m.end())
            if s:
                mult = SUFFIX_MULT.get(s.group(1), SUFFIX_MULT.get(s.group(1).lower(), 1))
                rs = {r * mult for r in rs}
                tok = tok + s.group(0)
            if all(abs(r) < 1e-12 for r in rs):
                continue
            if not any(supported(r, pool) for r in rs):
                unsupported.append({"line": ln_no, "number": tok.strip(), "text": line.strip()[:120]})
        for wm in WORD_NUM_RE.finditer(line):
            worded.append({"line": ln_no, "text": wm.group(0),
                           "issue": "cifra escrita en palabras: usar numeros para poder verificarla"})
        for bid in ID_RE.findall(line):
            if not DATE_NEAR_RE.search(line):
                missing_dates.append({"line": ln_no, "id": bid})
    ok = not unsupported and not missing_dates and not worded
    return {"ok": ok, "unsupported_numbers": unsupported, "numbers_in_words": worded,
            "benchmark_ids_without_date": missing_dates, "pool_size": len(pool)}


def main(argv):
    if len(argv) < 3:
        print("uso: python check_claims.py report.md evaluation.json")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    out = check(text, load_json(argv[2]))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
