import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import radar


class RadarTests(unittest.TestCase):
    def test_paid_or_unknown_prices_are_blocked(self):
        for m in [
            {'id': 'openrouter/auto', 'pricing': {'prompt': '0', 'completion': '0'}},
            {'id': 'vendor/model:free', 'pricing': {'prompt': '0', 'completion': '1'}},
            {'id': 'vendor/model:free', 'pricing': {'prompt': '0', 'completion': '0', 'request': '.01'}},
            {'id': 'vendor/model:free', 'pricing': {}},
            {'id': 'vendor/model:free', 'pricing': {'prompt': 'unknown', 'completion': '0'}}
        ]:
            self.assertFalse(radar.zero_priced(m))
        self.assertTrue(radar.zero_priced({'id': 'openrouter/free', 'pricing': {'prompt': '0', 'completion': '0'}}))

    def test_feed_rejects_future_old_undated_and_unsafe_entries(self):
        body = b'''<rss><channel>
        <item><title>fresh</title><link>https://example.com/a</link><pubDate>Wed, 14 Oct 2026 02:00:00 GMT</pubDate><description>summary</description></item>
        <item><title>future</title><link>https://example.com/b</link><pubDate>Thu, 15 Oct 2026 02:00:00 GMT</pubDate></item>
        <item><title>old</title><link>https://example.com/c</link><pubDate>Wed, 07 Oct 2026 02:00:00 GMT</pubDate></item>
        <item><title>undated</title><link>https://example.com/d</link></item>
        <item><title>unsafe</title><link>javascript:alert(1)</link><pubDate>Wed, 14 Oct 2026 02:00:00 GMT</pubDate></item>
        </channel></rss>'''
        now = datetime(2026, 10, 14, 3, tzinfo=timezone.utc)
        items = radar.parse_feed(body, {'name': 'test', 'url': 'https://example.com/rss'}, now, 48)
        self.assertEqual([i['title'] for i in items], ['fresh'])

    def test_delta_needs_a_real_comparable_snapshot(self):
        now = datetime(2026, 10, 14, tzinfo=timezone.utc)
        self.assertIsNone(radar.delta([], 'a/b', now, 1))
        h = [{'at': (now - timedelta(hours=4)).isoformat(), 'stars': {'a/b': 90}}]
        self.assertIsNone(radar.delta(h, 'a/b', now, 1))
        h.append({'at': (now - timedelta(hours=25)).isoformat(), 'stars': {'a/b': 80}})
        self.assertEqual(radar.delta(h, 'a/b', now, 1), 80)
        self.assertIsNone(radar.delta(h, 'a/b', now, 7))

    def test_hallucinated_links_rejected(self):
        items = [{'url': 'https://example.com/a'}]
        valid = '材料说明。' * 100 + '\n[来源](https://example.com/a)'
        self.assertEqual(radar.validate_report(valid, items), valid)
        with self.assertRaises(radar.RequestError):
            radar.validate_report(valid + '\nhttps://example.com/invented', items)

    def test_message_splits_keep_all_text_under_limit(self):
        text = ('一段中文文本\n' * 4000)
        parts = radar.split_message(text)
        self.assertTrue(all(len(p) <= 9000 for p in parts))
        self.assertEqual(''.join(parts).replace('\n', ''), text.replace('\n', ''))

    def test_ambiguous_send_is_not_retried(self):
        state = {'push_receipts': {'2026-10-14:ai:1': {'status': 'pending'}}}
        with patch.dict('os.environ', {'PUSHPLUS_TOKEN': 'test-token'}), patch('radar.get_json') as call:
            with self.assertRaises(radar.RequestError):
                radar.push_report('test', 'test body', state, 'ai', '2026-10-14')
            call.assert_not_called()

    def test_free_only_request_has_no_plugins_or_tools(self):
        state, now = {}, datetime(2026, 10, 14, tzinfo=timezone.utc)
        text = '来源材料说明。' * 100 + '[S01]'
        responses = [
            {'data': [{'id': 'openrouter/free', 'pricing': {'prompt': '0', 'completion': '0'}}]},
            {'data': {'free_model_daily_requests': {'remaining': 2}}},
            {'model': 'vendor/model:free', 'choices': [{'finish_reason': 'stop', 'message': {'content': text}}], 'usage': {'cost': 0}}
        ]
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}), patch('radar.get_json', side_effect=responses) as call, patch('radar.save_state'):
            radar.generate('ai', [{'url': 'https://example.com/a'}], {'model': 'openrouter/free'}, state, now)
            payload = call.call_args_list[2].args[1]
            self.assertEqual(payload['provider']['max_price'], {'prompt': 0, 'completion': 0})
            self.assertNotIn('plugins', payload)
            self.assertNotIn('tools', payload)
            self.assertNotIn('models', payload)
            self.assertEqual(payload['reasoning'], {'enabled': False})
            self.assertEqual(state['model_requests']['2026-10-14'], 1)

    def test_source_ids_restore_exact_urls_and_reject_unknown_sources(self):
        items = [{'url': 'https://example.com/very-long?query=original'}]
        self.assertEqual(radar.expand_citations('材料 [S01]', items),
                         '材料 [来源1](https://example.com/very-long?query=original)')
        for text in ['材料 [S02]', '材料 https://example.com/invented', '没有引用']:
            with self.assertRaises(radar.RequestError):
                radar.expand_citations(text, items)


if __name__ == '__main__':
    unittest.main()
