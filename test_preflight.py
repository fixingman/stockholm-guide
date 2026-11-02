"""Delivery checks must report missing and unreachable images as failures."""
import unittest
from preflight import Images, check_image, inspect

class PreflightTests(unittest.TestCase):
    def test_relative_email_image_is_rejected_without_network(self):
        def no_network(*args, **kwargs):
            self.fail('Relative URL should be rejected before a network request')
        self.assertFalse(check_image('assets/photo.jpg', opener=no_network)['ok'])

    def test_network_failure_cannot_be_hidden_by_a_snapshot(self):
        def unavailable(*args, **kwargs):
            raise OSError('upstream unavailable')
        result = check_image('https://example.com/photo.jpg', opener=unavailable)
        self.assertFalse(result['ok'])
        self.assertIn('upstream unavailable', result['error'])

    def test_loaded_placeholders_do_not_count_as_event_thumbnails(self):
        report = inspect('<img src="https://example.com/placeholder.jpg">',
                         {'top3': [{'title': 'Event'}], 'new_discoveries': []},
                         image_checker=lambda url: {'url': url, 'ok': True})
        self.assertFalse(report['ready_for_delivery'])
        self.assertEqual(report['unresolved_event_image_slots'][0]['title'], 'Event')

    def test_signed_query_order_and_background_urls_are_preserved(self):
        signed = 'https://example.com/photo?w=1440&h=810&auto=compress%2Cformat&s=signature'
        parser = Images()
        parser.feed('<td background="' + signed.replace('&', '&amp;') + '"></td>')
        self.assertEqual(parser.urls, [signed])
        def verify_request(request, **kwargs):
            self.assertEqual(request.full_url, signed)
            raise OSError('checked exact URL')
        self.assertIn('checked exact URL', check_image(signed, opener=verify_request)['error'])

if __name__ == '__main__':
    unittest.main()
