"""Untrusted-input scanner (RS-INJ-01/02): flags text aimed at AI agents inside proposals, annexes,
web pages, API responses and dataset text. Findings are recorded in evaluation.json
injection_findings[]; the instructions are NEVER followed. A finding does not change the verdict.

Patterns include those actually observed during the research (2026-11): Gemini pricing page
"AI Agent Context" block, OpenAI header note for agents, g2.com/ai-instructions, llms.txt indexes,
skill docs asking agents to write files, an OpenAlex response asking to create an API key, and
"Summary by AI" blocks. English, Spanish, French, Portuguese, Italian and German override phrases are
covered, and Base64 runs are decoded and re-scanned.

THIS IS A HEURISTIC TRIAGE AID, NOT A SECURITY BARRIER (independent audit REV-002): it will miss novel
or paraphrased injections. The real defence is the policy in references/untrusted-input-policy.md:
all retrieved content is data, never instructions, whether or not this scanner flags it.

Usage: python scan_injection.py <file> [<file> ...]   or   python scan_injection.py --stdin --origin URL
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import sys

ASSISTANT = r"(?:ai|a\.i\.|llm|language\s+model|assistant|chatbot|evaluator|model|agent)"
ASISTENTE = r"(?:ia|modelo|asistente|evaluador|agente|sistema)"
PATTERNS = [
    ("override", r"\b(ignore|disregard|forget)\s+(all\s+|any\s+)?(previous|prior|above|earlier|your)\s+(instructions|prompts?|rules)"),
    # Each override needs a previous-instructions reference or a second-person possessive, so business prose such
    # as "el cliente ignora las reglas de facturacion" is not flagged.
    ("override_es", r"\b(ignora|olvida|omite)\s+(todas\s+)?((las\s+)?(instrucciones|indicaciones|reglas)\s+(anteriores|previas)"
                    r"|tus\s+(instrucciones|indicaciones|reglas))"),
    ("override_fr", r"\b(ignore[rz]?|oublie[rz]?)\s+(toutes\s+)?((les\s+)?(instructions|consignes|r[eè]gles)\s+"
                    r"(pr[eé]c[eé]dentes|ant[eé]rieures)|(vos|tes)\s+(instructions|consignes|r[eè]gles))"),
    ("override_pt", r"\b(ignore|ignora|esque[cç]a)\s+(todas\s+)?((as\s+)?(instru[cç][oõ]es|regras)\s+anteriores"
                    r"|suas\s+(instru[cç][oõ]es|regras))"),
    ("override_it", r"\b(ignora|dimentica)\s+(tutte\s+)?((le\s+)?(istruzioni|regole)\s+precedenti|le\s+tue\s+istruzioni)"),
    ("override_de", r"\b(ignoriere|vergiss)\s+(alle\s+)?(vorherigen\s+|bisherigen\s+)?(anweisungen|regeln|instruktionen)"),
    ("agent_addressed", r"\b(if|when)\s+you\s+are\s+an?\s+" + ASSISTANT + r"\b"),
    ("agent_addressed_es", r"\bsi\s+eres\s+(un|una)\s+" + ASISTENTE + r"\b"),
    ("agent_context_block", r"\bai\s+agent\s+context\b|\bnote\s+(to|for)\s+(ai|llm|agents?)\b|\bfor\s+ai\s+agents\b"
                            r"|\bnota\s+para\s+(el\s+)?(asistente|agente|modelo|ia)\b"),
    ("llms_txt", r"\bllms(-full)?\.txt\b"),
    ("ai_instructions_page", r"\bai-instructions\b"),
    # Narrowed after REV-002: only second-person directives aimed at the assistant, not product copy such as
    # "nuestro agente actua como primer nivel de soporte".
    ("role_claim", r"\b(you\s+are\s+now|from\s+now\s+on\s+you\s+are|act\s+as\s+(an?\s+|the\s+)?" + ASSISTANT +
                   r"|(ahora|a\s+partir\s+de\s+ahora)\s+eres|act[uú]a\s+como\s+(un|una|el|la)\s+" + ASISTENTE + r")\b"),
    ("system_prompt", r"\b(system\s+prompt|developer\s+message|mensaje\s+del\s+sistema)\b"),
    ("credential_request", r"\b(create|generate|provide|send|crea|genera|env[ií]a)\b.{0,40}\b(api[\s_-]?key|token|password|contrase[ñn]a|clave\s+de\s+api)\b"),
    ("exfiltration", r"\b(send|post|upload|email|env[ií]a|sube)\b.{0,60}\b(to|a)\s+(https?://|[\w.-]+@[\w.-]+)"),
    ("verdict_tampering", r"\b(rate|score|grade|evaluate|califica|punt[uú]a|eval[uú]a)\b.{0,40}\b(as\s+)?(go|excellent|10/10|approved|aprobad[oa]|excelente|viable)\b.{0,30}\b(regardless|no\s+matter|sin\s+importar|siempre)\b"),
    ("tool_steering", r"\b(run|execute|call|use|ejecuta|llama|usa)\s+(the\s+)?(tool|command|bash|curl|webfetch|herramienta|comando)\b"),
    ("download_instruction", r"\b(download|fetch|visit|descarga|visita|abre)\s+(the\s+)?(following|this|esta|este|siguiente)?\s*(url|link|page|p[aá]gina|enlace|file|archivo)\b"),
    ("ai_summary_block", r"\bsummary\s+by\s+ai\b|\bresumen\s+(generado\s+)?por\s+ia\b"),
    ("file_write_request", r"\b(save|write|record|guarda|escribe|registra)\b.{0,40}\b(timing\.json|tokens?\s+and\s+time|cada\s+subagente)\b"),
]
HIDDEN = [
    ("zero_width", "[​‌‍⁠﻿]"),
    ("html_comment", r"<!--.*?-->"),
    ("invisible_style", r"(color\s*:\s*(#fff(fff)?|white)|font-size\s*:\s*0|display\s*:\s*none)"),
]
_C = [(n, re.compile(p, re.I | re.S)) for n, p in PATTERNS + HIDDEN]


def _snippet(text, start, end, words=15):
    s = text[max(0, start - 40): end + 40].replace("\n", " ")
    return " ".join(s.split()[:words])


B64_RE = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


def _decoded_base64(text: str):
    """Yield (offset, decoded_text) for Base64 runs that decode to mostly printable UTF-8."""
    for m in B64_RE.finditer(text):
        chunk = m.group(0)
        try:
            raw = base64.b64decode(chunk + "=" * (-len(chunk) % 4), validate=True)
            dec = raw.decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
        if dec and sum(c.isprintable() or c.isspace() for c in dec) / len(dec) > 0.9:
            yield m.start(), dec


def scan_text(text: str, origin: str, _depth: int = 0) -> list[dict]:
    found = []
    for name, rx in _C:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            found.append({"origin": origin, "line": line, "pattern": name,
                          "snippet": _snippet(text, m.start(), m.end()), "action": "ignored (data, not instruction)"})
    if _depth == 0:
        for offset, dec in _decoded_base64(text):
            for f in scan_text(dec, origin, _depth=1):
                f.update(line=text.count("\n", 0, offset) + 1, pattern="base64:" + f["pattern"],
                         snippet="[decodificado] " + f["snippet"])
                found.append(f)
    seen, out = set(), []
    for f in found:
        k = (f["origin"], f["line"], f["pattern"])
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass
    findings = []
    if "--stdin" in argv:
        origin = argv[argv.index("--origin") + 1] if "--origin" in argv else "stdin"
        findings = scan_text(sys.stdin.read(), origin)
    else:
        for p in argv[1:]:
            with open(p, encoding="utf-8", errors="replace") as fh:
                findings += scan_text(fh.read(), p)
    print(json.dumps({"injection_findings": findings, "count": len(findings)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
