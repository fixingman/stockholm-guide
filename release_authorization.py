"""Fail-closed delivery authorization; no network access or subscriber data.

Public CI validates and stages artifacts. The private mail agent is separately
responsible for isolated test-inbox delivery and read-back before subscriber send.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr

OWNER = "cankilicbay@gmail.com"

def clean_address(address):
    name, value = parseaddr(address or "")
    return value.lower() if not name and value else ""

def verify_release(manifest, issue, *, channel):
    errors=[]
    if manifest.get("release_channel") != channel:
        errors.append("Release channel mismatch")
    if manifest.get("ready_for_delivery") is not True:
        errors.append("Preflight not ready")
    if manifest.get("issue_number") != issue.get("issue_number"):
        errors.append("Issue mismatch")
    if manifest.get("date_range") != issue.get("date_range"):
        errors.append("Date range mismatch")
    if not manifest.get("source_commit_sha") or manifest["source_commit_sha"] == "unknown":
        errors.append("Missing immutable source SHA")
    if not manifest.get("html_sha256"):
        errors.append("Missing HTML digest")
    if not manifest.get("editorial_quality",{}).get("ready_for_editorial_release"):
        errors.append("Strict editorial check not passed")
    if not manifest.get("freshness",{}).get("ready_for_send"):
        errors.append("Freshness check not passed")
    if len(manifest.get("featured_images",[])) != 3 or manifest.get("inline_fallbacks") != 0:
        errors.append("Three real photos and zero fallback tiles required")
    checks=manifest.get("image_checks",[])
    if len(checks) != 3 or not all(c.get("ok") is True for c in checks):
        errors.append("Three successful live image checks required")
    if channel == "production" and issue.get("rehearsal") is True:
        errors.append("Rehearsal cannot be production")
    if channel == "smoke" and not (issue.get("rehearsal") is True and issue.get("visual_test") is True):
        errors.append("Only explicitly marked owner-only visual rehearsals qualify")
    return errors

def verify_test_delivery(release, *, to, cc=(), bcc=(), message_id=None,
                         received_html_sha256=None, received=False, subject=""):
    errors=[]
    if [clean_address(x) for x in to] != [OWNER] or cc or bcc:
        errors.append("Private test MUST go only to owner, no CC/BCC")
    if not subject.startswith("[TEST]"):
        errors.append("Test subject must be labelled")
    if not message_id or not received:
        errors.append("Test inbox receipt has not been verified")
    if not received_html_sha256 or received_html_sha256 != release.get("html_sha256"):
        errors.append("Test inbox HTML mismatch")
    return errors

def production_authorization(manifest, issue, test_receipt, *, duplicate_sent=False):
    errors=verify_release(manifest, issue, channel="production")
    if not isinstance(test_receipt,dict):
        errors.append("No private owner-only staging receipt")
    else:
        if test_receipt.get("source_commit_sha") != manifest.get("source_commit_sha"):
            errors.append("Staging receipt belongs to a different source commit")
        if test_receipt.get("html_sha256") != manifest.get("html_sha256"):
            errors.append("Staging receipt HTML differs from production artifact")
        errors.extend(verify_test_delivery(manifest,to=test_receipt.get("to",[]),
                     cc=test_receipt.get("cc",[]),bcc=test_receipt.get("bcc",[]),
                     message_id=test_receipt.get("message_id"),
                     received_html_sha256=test_receipt.get("received_html_sha256"),
                     received=test_receipt.get("received") is True,
                     subject=test_receipt.get("subject","")))
    if duplicate_sent:
        errors.append("Already sent: refuse duplicate")
    return errors
