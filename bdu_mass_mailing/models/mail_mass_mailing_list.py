# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import safe_eval
from odoo.exceptions import UserError

class MassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    def action_sync(self):
        """Sync contacts in dynamic lists."""
        Contact = self.env["mail.mass_mailing.contact"].with_context(
            syncing=True,
        )
        Partner = self.env["res.partner"]
        # Skip non-dynamic lists
        dynamic = self.filtered("dynamic")
        for one in dynamic:
            sync_domain = safe_eval(one.sync_domain) + [("email", "!=", False)]
            desired_partners = Partner.search(sync_domain)
            if one.sync_method == "full":
                Contact.search([
                    ("list_id", "=", one.id),
                    ("partner_id", "not in", desired_partners.ids),
                ]).unlink()
            current_contacts = Contact.search([("list_id", "=", one.id)])
            current_partners = current_contacts.mapped("partner_id")
            # Add new contacts
            currentdt = fields.Datetime.to_string(fields.datetime.now())
            values = []
            for partner in desired_partners - current_partners:
                email = partner.email.encode("utf-8").replace("'", "-").replace('"', '-')
                name = partner.name.encode("utf-8").replace("'", "-").replace('"', '-')
                values.append((str(email), partner.id, str(name), one.id, False, self._uid, str(currentdt), self._uid, str(currentdt)))
            if values:
                query_prefix = "INSERT INTO mail_mass_mailing_contact (email, partner_id, name, list_id, opt_out, create_uid, create_date, write_uid, write_date) VALUES "
                query = query_prefix + str(values)[1:-1]
                try:
                    self.env.cr.execute(query)
                except:
                    raise UserError(_("Please check the selected partners."))

            one.is_synced = True
        # Invalidate cached contact count
        self.invalidate_cache(["contact_nbr"], dynamic.ids)