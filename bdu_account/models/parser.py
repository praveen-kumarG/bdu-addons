# -*- coding: utf-8 -*-
"""Class to parse camt files."""
# © 2013-2016 Therp BV <http://therp.nl>
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import re
from lxml import etree

from odoo import models


class CamtParser(models.AbstractModel):
    _inherit = 'account.bank.statement.import.camt.parser'
    """Parser for camt bank statement import files."""


    def parse_transaction_details(self, ns, node, transaction):
        """Parse TxDtls node."""
        super(CamtParser, self).parse_transaction_details(ns, node, transaction)
        name = transaction['name']
        transaction['name'] = transaction['note']
        transaction['note'] = name
