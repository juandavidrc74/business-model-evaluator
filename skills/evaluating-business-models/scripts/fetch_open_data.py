"""Free open-data fetcher (RF-GEO-05/06, RS-INJ-02, RS-SEC-04). No API keys, no accounts, no paid data.

Only allow-listed hosts and dataset ids are reachable; the script never follows URLs found inside
responses. Every response is scanned with scan_injection before being returned, and the result
carries access_date so it can enter the Evidence Ledger (tier 1, retrieved_by_tool = true).

SEC EDGAR requires a User-Agent with a contact that the USER configures in the environment variable
BME_SEC_USER_AGENT (e.g. "Nombre Apellido correo@dominio"); the skill never invents one and refuses
SEC calls without it.

Usage:
    python fetch_open_data.py worldbank COL NY.GDP.MKTP.KD.ZG
    python fetch_open_data.py imf PCPIPCH COL
    python fetch_open_data.py socrata 32sa-8pi3 '$limit=5&$order=vigenciadesde DESC'
    python fetch_open_data.py sec_companyfacts 0001467373
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

from scan_injection import scan_text

TIMEOUT = 30
ALLOWED_HOSTS = {"api.worldbank.org", "www.imf.org", "www.datos.gov.co", "data.sec.gov"}
SOCRATA_DATASETS = {
    "32sa-8pi3": "TRM (Superfinanciera)",
    "qzsc-9esp": "Tasas de credito por modalidad (Superfinanciera)",
    "w9zh-vetq": "Tasas de credito por CIIU/tamano (Superfinanciera)",
    "prwj-nzxa": "Estados financieros NIIF - Supersociedades",
    "pfdp-zks5": "Estados financieros NIIF - Supersociedades",
    "ctcp-462n": "Estados financieros NIIF - Supersociedades",
    "6cat-2gcs": "10.000 empresas mas grandes con CIIU - Supersociedades",
}
WEB_CALL_BUDGET = 30  # default per evaluation [P]; the model records web_calls in evaluation.json


class _AllowListRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only if the target is HTTPS and on the allow-list (audit R4: urllib follows
    redirects by default, which could otherwise reach a host outside the list)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"Redireccion bloqueada hacia {parsed.hostname!r}: fuera de la lista de fuentes abiertas")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_AllowListRedirects)


def _get(url: str, headers: dict | None = None) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host no permitido: {parsed.hostname} (solo fuentes abiertas de la lista, por HTTPS)")
    req = urllib.request.Request(url, headers={"User-Agent": "business-model-evaluator/1.0 (open-data fetch)",
                                               **(headers or {})})
    with _OPENER.open(req, timeout=TIMEOUT) as r:  # noqa: S310 (allow-listed hosts only, redirects checked)
        body = r.read().decode("utf-8", errors="replace")
    findings = scan_text(body, url)
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = body[:2000]
    return {"url": url, "access_date": dt.date.today().isoformat(), "retrieved_by_tool": True,
            "injection_findings": findings, "data": data,
            "ledger_hint": {"source": {"type": "api", "tier": 1, "url": url}, "retrieved_by_tool": True}}


def worldbank(country: str, indicator: str, per_page: int = 20):
    url = (f"https://api.worldbank.org/v2/country/{urllib.parse.quote(country)}/indicator/"
           f"{urllib.parse.quote(indicator)}?format=json&per_page={int(per_page)}")
    return _get(url)


def imf(indicator: str, country: str):
    return _get(f"https://www.imf.org/external/datamapper/api/v1/{urllib.parse.quote(indicator)}/"
                f"{urllib.parse.quote(country)}")


def socrata(dataset: str, query: str = "$limit=10"):
    if dataset not in SOCRATA_DATASETS:
        raise ValueError(f"Dataset no permitido: {dataset}. Permitidos: {sorted(SOCRATA_DATASETS)}")
    q = urllib.parse.quote(query, safe="=&$,' ")
    return _get(f"https://www.datos.gov.co/resource/{dataset}.json?{q.replace(' ', '%20')}")


def sec_companyfacts(cik: str):
    ua = os.environ.get("BME_SEC_USER_AGENT")
    if not ua:
        raise ValueError("SEC exige un User-Agent con contacto: el usuario debe definir BME_SEC_USER_AGENT. "
                         "La Skill no inventa ni usa datos personales para esto.")
    cik10 = str(int(cik)).zfill(10)
    return _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json", {"User-Agent": ua})


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    fns = {"worldbank": worldbank, "imf": imf, "socrata": socrata, "sec_companyfacts": sec_companyfacts}
    if cmd not in fns:
        print(json.dumps({"error": f"fuente desconocida {cmd}", "sources": list(fns)}))
        return 2
    try:
        out = fns[cmd](*args)
    except Exception as exc:  # network errors are reported, never retried against other hosts
        print(json.dumps({"error": str(exc), "recorded_as": "unknown"}, ensure_ascii=False))
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2)[:200_000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
