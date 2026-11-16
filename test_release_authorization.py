"""Fail-closed release and recipient isolation regression tests."""
import unittest
from release_authorization import (verify_release, verify_test_delivery,
                                   production_authorization)


def fixture():
    issue={"issue_number":"005","date_range":"22 Nov–5 Dec"}
    manifest={"release_channel":"production","ready_for_delivery":True,
              "issue_number":"005","date_range":"22 Nov–5 Dec",
              "source_commit_sha":"abc012","html_sha256":"digest-valid",
              "editorial_quality":{"ready_for_editorial_release":True},
              "freshness":{"ready_for_send":True},
              "featured_images":["https://example.org/one.jpg",
                                 "https://example.org/two.jpg",
                                 "https://example.org/three.jpg"],
              "inline_fallbacks":0,
              "image_checks":[{"ok":True},{"ok":True},{"ok":True}]}
    receipt={"source_commit_sha":"abc012","html_sha256":"digest-valid",
             "to":["owner@example.org"],"cc":[],"bcc":[],"message_id":"sent-id",
             "received_html_sha256":"digest-valid","received":True,
             "subject":"[TEST] Stockholm Guide"}
    return issue,manifest,receipt


class ReleaseAuthorizationTests(unittest.TestCase):
    def test_valid_release_plus_private_test_inbox_passes(self):
        issue,manifest,receipt=fixture()
        self.assertEqual(production_authorization(manifest,issue,receipt,owner="owner@example.org"),[])

    def test_missing_test_inbox_receipt_blocks_production(self):
        issue,manifest,receipt=fixture()
        self.assertTrue(production_authorization(manifest,issue,None,owner="owner@example.org"))
        receipt["received"]=False
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_test_message_with_bcc_is_rejected(self):
        issue,manifest,receipt=fixture()
        receipt["bcc"]=["subscriber@example.com"]
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_wrong_test_recipient_or_cc_is_rejected(self):
        issue,manifest,receipt=fixture()
        receipt["to"]=["subscriber@example.com"]
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))
        receipt["to"]=["owner@example.org"]
        receipt["cc"]=["subscriber@example.com"]
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_stale_or_different_html_does_not_authorize(self):
        issue,manifest,receipt=fixture()
        receipt["source_commit_sha"]="other"
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))
        receipt["source_commit_sha"]="abc012"
        receipt["received_html_sha256"]="different"
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_missing_or_failed_photos_block(self):
        issue,manifest,receipt=fixture()
        manifest["inline_fallbacks"]=1
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))
        manifest["inline_fallbacks"]=0
        manifest["image_checks"][2]["ok"]=False
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_duplicate_sent_blocks(self):
        issue,manifest,receipt=fixture()
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org",duplicate_sent=True))

    def test_rehearsal_never_eligible_for_production(self):
        issue,manifest,receipt=fixture()
        issue["rehearsal"]=True
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))

    def test_missing_editorial_freshness_or_channel_blocks(self):
        issue,manifest,receipt=fixture()
        manifest["editorial_quality"]["ready_for_editorial_release"]=False
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))
        manifest["editorial_quality"]["ready_for_editorial_release"]=True
        manifest["release_channel"]="smoke"
        self.assertTrue(production_authorization(manifest,issue,receipt,owner="owner@example.org"))


class ArtifactAuthorizationTests(unittest.TestCase):
    def test_exact_artifacts_pass_and_tampering_blocks(self):
        from release_authorization import authorize_artifacts
        from delivery_guard import html_digest
        issue, manifest, receipt = fixture()
        html = '<html>approved</html>'
        digest = html_digest(html)
        manifest['html_sha256'] = digest
        receipt.update(html_sha256=digest, received_html_sha256=digest)
        client = {'ok': True, 'html_sha256': digest, 'browser_scenarios': [
            {'width': w, 'scheme': s, 'ok': True}
            for w in (320, 390, 650) for s in ('light', 'dark')]}
        visual = {'ok': True, 'html_sha256': digest, 'visual_scenarios': [
            {'width': w, 'scheme': s, 'ok': True}
            for w, s in ((390, 'light'), (390, 'dark'), (650, 'light'))]}
        def check(**changes):
            args = dict(owner='owner@example.org', html=html,
                        client_qa=client, visual_qa=visual)
            args.update(changes)
            return authorize_artifacts(manifest, issue, receipt, **args)
        self.assertEqual(check(), [])
        self.assertTrue(check(html=html + 'changed'))
        self.assertTrue(check(visual_qa=None))
        self.assertTrue(check(duplicate_sent=True))
        visual['html_sha256'] = 'old-artifact'
        self.assertTrue(check())
        visual['html_sha256'] = digest
        visual['visual_scenarios'][0]['ok'] = False
        self.assertTrue(check())
        visual['visual_scenarios'][0]['ok'] = True
        visual['visual_scenarios'][1] = visual['visual_scenarios'][0]
        self.assertTrue(check())


class VisualDimensionsTests(unittest.TestCase):
    def test_mobile_design_size_passes_but_missing_or_collapsed_photo_fails(self):
        from email_client_qa import visual_result_ok
        row = {'photoCount': 3, 'fallbackCount': 0, 'overflow': False,
               'photoDetails': [dict(complete=True, naturalWidth=750,
                    naturalHeight=750, width=76, height=76) for _ in range(3)]}
        self.assertTrue(visual_result_ok(row, 390))
        self.assertFalse(visual_result_ok(row, 650))
        row['photoDetails'][0]['naturalWidth'] = 0
        self.assertFalse(visual_result_ok(row, 390))
        row['photoDetails'][0]['naturalWidth'] = 750
        row['photoDetails'][0]['width'] = 0
        self.assertFalse(visual_result_ok(row, 390))
        row['photoDetails'][0]['width'] = 76
        row['fallbackCount'] = 1
        self.assertFalse(visual_result_ok(row, 390))
        row['fallbackCount'] = 0
        row['overflow'] = True
        self.assertFalse(visual_result_ok(row, 390))


if __name__ == "__main__":
    unittest.main()
