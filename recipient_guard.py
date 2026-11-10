#!/usr/bin/env python3
"""Private newsletter recipient and sending-policy preflight.

Never commit subscriber/suppression JSON to GitHub. No email is ever sent.
A signed-off Gmail account still must enforce actual consent and unsubscribe.
"""
import argparse
import json
import re
from pathlib import Path
from email.utils import parseaddr

ADDRESS=re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}$")


def canonical(value):
    name,addr=parseaddr(value or "")
    return addr.lower().strip() if not name and ADDRESS.fullmatch(addr) else ""


def audit(*,to,cc=(),bcc=(),suppressed=(),consented=(),mode="scheduled",
          require_consent=True,unsubscribe_mailbox=None,from_address=None):
    to=[canonical(x) for x in to]
    cc=[canonical(x) for x in cc]
    bcc=[canonical(x) for x in bcc]
    blocked={canonical(x) for x in suppressed}
    consents={canonical(x) for x in consented}
    recipients=to+cc+bcc
    errors=[];warnings=[]
    if not recipients or not all(recipients):
        errors.append("Missing or invalid recipient")
    if len(recipients)!=len(set(recipients)):
        errors.append("Duplicate recipient appears in To/CC/BCC")
    if set(recipients)&blocked:
        errors.append("Recipient is on suppression/unsubscribe list")
    if require_consent and set(recipients)-consents:
        errors.append("Recipients lacking documented consent: "+str(len(set(recipients)-consents)))
    if mode not in ("scheduled","test"):
        errors.append("Unknown delivery mode")
    if mode=="test" and bcc:
        errors.append("Test messages MUST NOT have any BCC recipient")
    if mode=="test" and cc:
        errors.append("Test messages MUST NOT have CC recipients")
    if mode=="scheduled" and len(to)!=1:
        errors.append("Scheduled newsletter requires exactly one owner To address")
    if not canonical(unsubscribe_mailbox):
        errors.append("No working unsubscribe mailbox configured")
    if from_address and not canonical(from_address):
        errors.append("Invalid sender address")
    warnings.append("SPF, DKIM, DMARC, inbox placement and bounce processing require provider-side checks")
    return {"ready_for_send":not errors,"errors":errors,"warnings":warnings,
            "recipient_count":len(recipients),"bcc_count":len(bcc),
            "mode":mode,
            "note":"Local data validation only; no messages sent."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config",required=True,help="PRIVATE JSON outside repository")
    p.add_argument("--report",default="recipient-audit.json")
    args=p.parse_args()
    config=json.loads(Path(args.config).read_text())
    report=audit(**config)
    Path(args.report).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["ready_for_send"] else 1


if __name__=="__main__":
    raise SystemExit(main())
