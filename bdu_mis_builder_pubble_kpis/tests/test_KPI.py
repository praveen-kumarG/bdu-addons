# _*_ codeing: utf-8 _*_
from odoo.tests.common import TransactionCase

class TestKPI(TransactionCase):

	def test_create(self):
		"Create a KPI"
		KPI = self.env['kpi.data']
		kpi = KPI.create({'key': 'aantal_advertentiepaginas', 'value':'16'})
		self.assertEqual(kpi.value, 16)
		