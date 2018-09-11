# _*_ codeing: utf-8 _*_
from odoo.tests.common import TransactionCase

class TestPOIO(TransactionCase):

	def test_poio_config(self):
		"Check config"
		poio = self.env['poio.config']
		message = poio.test_order_connection()
		self.assertEqual(message, "OK")
		