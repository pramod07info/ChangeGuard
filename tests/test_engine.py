import unittest
from engine import analyze


class ImpactTests(unittest.TestCase):
    def payload(self):
        return dict(service='payments', before={'GET /payments': {'id': 'string', 'amount': 'number'}}, after={'GET /payments': {'id': 'string'}}, dependencies={'orders': ['payments'], 'storefront': ['orders'], 'payments': ['storefront']})

    def test_removal_and_transitive_cycle(self):
        result = analyze(self.payload())
        self.assertEqual(result['risk'], 'HIGH')
        self.assertEqual(result['breakingChanges'][0]['code'], 'RESPONSE_FIELD_REMOVED')
        self.assertEqual([s['service'] for s in result['potentialConsumers']], ['orders', 'storefront'])
        self.assertEqual(result['potentialConsumers'][1]['path'], ['payments', 'orders', 'storefront'])

    def test_endpoint_removed(self):
        p = self.payload(); p['after'] = {}
        self.assertEqual(analyze(p)['breakingChanges'][0]['code'], 'ENDPOINT_REMOVED')

    def test_type_change(self):
        p = self.payload(); p['after'] = {'GET /payments': {'id': 'integer', 'amount': 'number'}}
        self.assertEqual(analyze(p)['breakingChanges'][0]['code'], 'RESPONSE_TYPE_CHANGED')

    def test_unchanged(self):
        p = self.payload(); p['after'] = p['before']
        self.assertEqual(analyze(p)['risk'], 'NONE')
        self.assertEqual(analyze(p)['potentialConsumers'], [])

    def test_additive(self):
        p = self.payload(); p['before'] = p['after']; p['after'] = {'GET /payments': {'id': 'string', 'status': 'string'}}
        self.assertEqual(analyze(p)['risk'], 'LOW')
        self.assertFalse(analyze(p)['requiresReview'])

    def test_invalid_inputs(self):
        for value in (None, [], {}, {'service': 'payments', 'before': [], 'after': {}}):
            with self.assertRaises(ValueError): analyze(value)

    def test_invalid_graph(self):
        p = self.payload(); p['dependencies'] = {'orders': 'payments'}
        with self.assertRaises(ValueError): analyze(p)

    def test_unknown_type(self):
        p = self.payload(); p['after'] = {'GET /payments': {'id': 'uuid'}}
        with self.assertRaises(ValueError): analyze(p)
