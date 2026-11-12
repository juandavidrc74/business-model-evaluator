# -*- coding: utf-8 -*-
"""Validate the benchmark database (standard library only).

Usage: python validate_benchmarks.py [path_to_json] [--due YYYY-MM-DD]
Default path: the skill's own assets/benchmarks.json, resolved relative to this script (portable).
Exit code 0 if all checks pass, 1 otherwise.
"""
import collections
import datetime as dt
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "benchmarks.json")

REQUIRED = ["id", "metric", "value", "value_low", "value_high", "value_text", "unit", "publication_date",
            "reference_period", "country", "archetype", "modifiers", "sector", "sample_size", "sample_note",
            "definition", "source", "url", "limitations", "evidence_quality", "tag", "next_review", "status",
            "supersedes", "superseded_by", "note_file", "usable_as_gate_threshold", "rule_of_thumb",
            "missing_fields", "compiler_notes"]
# Phase-2 final taxonomy (main report 6a): AI agent execution is the modifier AIX, never an archetype.
ARCH = {"S1", "S2", "S3", "S4", "P-SAAS-SS", "P-SAAS-SL", "P-USAGE", "P-AI-APP", "P-INFRA", "P-MKT", "general"}
MODS = {"V", "AIX"}
EQ = {"A", "B", "C"}
TAGS = {"[D]", "[S]", "[M]", "[I]", "[P]"}
STATUS = {"current", "superseded", "conflict", "withdrawn", "proposal"}
ISO = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
NULLABLE_MISSING = {"publication_date", "reference_period", "country", "definition", "source", "url", "limitations"}


def parse_iso(s):
    """ISO date/month/year -> date (month/year = first day). None if invalid."""
    if not isinstance(s, str):
        return None
    m = ISO.match(s)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def main(argv):
    path = DEFAULT
    due = dt.date(2027, 2, 28)
    args = list(argv[1:])
    if "--due" in args:
        i = args.index("--due")
        due = parse_iso(args[i + 1])
        del args[i:i + 2]
    if args:
        path = args[0]

    errors, warnings = [], []
    try:
        with open(path, encoding="utf-8") as f:
            db = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: cannot load JSON: {e}")
        return 1

    for k in ("schema_version", "generated", "description", "field_definitions", "archetype_codes",
              "modifier_codes", "benchmarks"):
        if k not in db:
            errors.append(f"top level: missing '{k}'")
    if isinstance(db.get("archetype_codes"), dict) and set(db["archetype_codes"]) != ARCH:
        errors.append(f"archetype_codes {sorted(db['archetype_codes'])} != validator enum {sorted(ARCH)}")
    if isinstance(db.get("modifier_codes"), dict) and set(db["modifier_codes"]) != MODS:
        errors.append(f"modifier_codes {sorted(db['modifier_codes'])} != validator enum {sorted(MODS)}")
    recs = db.get("benchmarks", [])
    if not isinstance(recs, list) or not recs:
        errors.append("benchmarks must be a non-empty list")
        recs = []
    for f in REQUIRED:
        if f not in db.get("field_definitions", {}):
            warnings.append(f"field_definitions lacks '{f}'")

    ids = [r.get("id") for r in recs]
    dup = [i for i, c in collections.Counter(ids).items() if c > 1]
    if dup:
        errors.append(f"duplicate ids: {dup}")
    idset = set(ids)

    for r in recs:
        rid = r.get("id", "<no id>")
        miss = [f for f in REQUIRED if f not in r]
        if miss:
            errors.append(f"{rid}: missing fields {miss}")
            continue
        extra = [f for f in r if f not in REQUIRED]
        if extra:
            warnings.append(f"{rid}: unexpected fields {extra}")
        for f in ("id", "metric", "unit", "sector", "note_file"):
            if not isinstance(r[f], str) or not r[f].strip():
                errors.append(f"{rid}: '{f}' must be a non-empty string")
        # values
        for f in ("value", "value_low", "value_high", "sample_size"):
            if r[f] is not None and not is_num(r[f]):
                errors.append(f"{rid}: '{f}' must be a number or null")
        if (r["value_low"] is None) != (r["value_high"] is None):
            errors.append(f"{rid}: value_low/value_high must both be set or both null")
        if is_num(r["value_low"]) and is_num(r["value_high"]) and r["value_low"] > r["value_high"]:
            errors.append(f"{rid}: value_low > value_high")
        if r["value"] is None and r["value_low"] is None and not r["value_text"]:
            errors.append(f"{rid}: no value, no range and no value_text")
        # enums
        if not isinstance(r["archetype"], list) or not r["archetype"]:
            errors.append(f"{rid}: archetype must be a non-empty list")
        else:
            bad = [a for a in r["archetype"] if a not in ARCH]
            if bad:
                errors.append(f"{rid}: invalid archetype codes {bad}")
            if "general" in r["archetype"] and len(r["archetype"]) > 1:
                warnings.append(f"{rid}: 'general' combined with specific archetypes {r['archetype']}")
        if not isinstance(r["modifiers"], list):
            errors.append(f"{rid}: modifiers must be a list")
        else:
            badm = [m for m in r["modifiers"] if m not in MODS]
            if badm:
                errors.append(f"{rid}: invalid modifier codes {badm}")
            if len(set(r["modifiers"])) != len(r["modifiers"]):
                errors.append(f"{rid}: duplicate modifier codes {r['modifiers']}")
        if r["evidence_quality"] not in EQ:
            errors.append(f"{rid}: evidence_quality '{r['evidence_quality']}' not in {sorted(EQ)}")
        if r["tag"] not in TAGS:
            errors.append(f"{rid}: tag '{r['tag']}' not in {sorted(TAGS)}")
        if r["status"] not in STATUS:
            errors.append(f"{rid}: status '{r['status']}' not in {sorted(STATUS)}")
        if r["tag"] == "[P]" and r["status"] != "proposal":
            errors.append(f"{rid}: tag [P] requires status 'proposal'")
        if r["status"] == "proposal" and r["tag"] != "[P]":
            errors.append(f"{rid}: status 'proposal' requires tag [P]")
        # url
        if r["url"] is None:
            if "url" not in r["missing_fields"]:
                errors.append(f"{rid}: url is null but not listed in missing_fields")
        elif not (isinstance(r["url"], str) and r["url"].lower().startswith("http")):
            errors.append(f"{rid}: url does not start with http: {r['url']!r}")
        # missing_fields consistency
        if not isinstance(r["missing_fields"], list):
            errors.append(f"{rid}: missing_fields must be a list")
        else:
            for f in r["missing_fields"]:
                if f not in NULLABLE_MISSING:
                    errors.append(f"{rid}: missing_fields lists unexpected field '{f}'")
                elif r.get(f) is not None:
                    errors.append(f"{rid}: '{f}' listed as missing but is not null")
        if not isinstance(r["compiler_notes"], list):
            errors.append(f"{rid}: compiler_notes must be a list")
        if not isinstance(r["rule_of_thumb"], bool) or not isinstance(r["usable_as_gate_threshold"], bool):
            errors.append(f"{rid}: rule_of_thumb and usable_as_gate_threshold must be booleans")
        # gate rule
        expected = (r["evidence_quality"] in ("A", "B") and r["tag"] == "[D]" and r["status"] == "current"
                    and not r["rule_of_thumb"] and r["url"] is not None)
        if r["usable_as_gate_threshold"] != expected:
            errors.append(f"{rid}: usable_as_gate_threshold={r['usable_as_gate_threshold']} violates rule (expected {expected})")
        # pointers
        for f in ("supersedes", "superseded_by"):
            v = r[f]
            if v is None:
                continue
            if not isinstance(v, list) or not v:
                errors.append(f"{rid}: '{f}' must be null or a non-empty list of ids")
                continue
            for t in v:
                if t not in idset:
                    errors.append(f"{rid}: '{f}' points to unknown id {t}")
                elif t == rid:
                    errors.append(f"{rid}: '{f}' points to itself")
        if r["status"] in ("superseded", "withdrawn", "conflict") and not r["superseded_by"]:
            errors.append(f"{rid}: status '{r['status']}' requires superseded_by")
        if r["status"] == "current" and r["superseded_by"]:
            errors.append(f"{rid}: status 'current' but superseded_by is set")
        # dates
        if parse_iso(r["next_review"]) is None:
            errors.append(f"{rid}: next_review is not an ISO date: {r['next_review']!r}")
        pdv = r["publication_date"]
        if pdv is not None and parse_iso(pdv) is None:
            warnings.append(f"{rid}: publication_date kept as text: {pdv!r}")

    # back-pointer symmetry
    by = {r["id"]: r for r in recs if "id" in r}
    for r in recs:
        for t in (r.get("superseded_by") or []):
            if t in by and r["id"] not in (by[t].get("supersedes") or []):
                errors.append(f"{r['id']}: superseded_by {t} but {t}.supersedes lacks it")

    # ---------- summary ----------
    print(f"File: {path}")
    print(f"schema_version={db.get('schema_version')} generated={db.get('generated')} records={len(recs)}")

    def show(title, counter):
        print(f"\n{title}:")
        for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))):
            print(f"  {k:<20} {v}")

    show("By archetype (a record can count in several)", collections.Counter(a for r in recs for a in r.get("archetype", [])))
    show("By modifier", collections.Counter(m for r in recs for m in (r.get("modifiers") or [])))
    show("By evidence_quality", collections.Counter(r.get("evidence_quality") for r in recs))
    show("By tag", collections.Counter(r.get("tag") for r in recs))
    show("By status", collections.Counter(r.get("status") for r in recs))
    show("By ID prefix", collections.Counter(r["id"].split("-")[0] for r in recs))
    print(f"\nusable_as_gate_threshold = true: {sum(1 for r in recs if r.get('usable_as_gate_threshold'))}")
    print(f"rule_of_thumb = true: {sum(1 for r in recs if r.get('rule_of_thumb'))}")
    print(f"records with missing_fields: {sum(1 for r in recs if r.get('missing_fields'))}")

    dueL = sorted((parse_iso(r["next_review"]), r["id"], r["next_review"], r["status"], r["metric"])
                  for r in recs if parse_iso(r.get("next_review")) and parse_iso(r["next_review"]) <= due)
    print(f"\nnext_review on or before {due.isoformat()}: {len(dueL)} records")
    for _, rid, nr, st, metric in dueL:
        print(f"  {nr:<10} {rid:<8} {st:<10} {metric[:80]}")

    print(f"\nWarnings: {len(warnings)}")
    for w in warnings:
        print("  WARN", w)
    print(f"\nErrors: {len(errors)}")
    for e in errors:
        print("  ERROR", e)
    print("\nRESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
