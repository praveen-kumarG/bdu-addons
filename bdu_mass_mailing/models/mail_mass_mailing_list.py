# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

class MassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    def action_sync(self):
        """Sync contacts in dynamic lists."""
        # Skip non-dynamic lists
        dynamic = self.filtered("dynamic")
        for one in dynamic:
            sync_domain = safe_eval(one.sync_domain) + [("email", "!=", False),'|',
                                                        ('company_id','=', False),('company_id','child_of', self.env.user.company_id.id)]

            # Remove undesired contacts when synchronization is full
            if one.sync_method == "full":
                del_query = ('''DELETE FROM mail_mass_mailing_contact
                            WHERE list_id = %s ''')
                self.env.cr.execute(del_query, [one.id])
            if sync_domain:
                query = self.env['res.partner']._where_calc(sync_domain)
                tables, where_clause, where_clause_params = query.get_sql()
                sync_query = ('''INSERT INTO mail_mass_mailing_contact
                                (email, partner_id, user_id, sector_id, name, list_id, opt_out, create_uid, create_date, write_uid, write_date)
                                SELECT email as email,
                                       id as partner_id,
                                       user_id as user_id,
                                       sector_id as sector_id,
                                       name as name,
                                       {0} as list_id,
                                       {1} as opt_out,
                                       {2} as create_uid,
                                       {3} as create_date,
                                       {2} as write_uid,
                                       {3} as write_date
                                FROM {4}
                                WHERE {5}
                                AND id not in 
                                (SELECT partner_id
                                FROM mail_mass_mailing_contact
                                WHERE list_id = {0});      
                                '''.format(
                                one.id,
                                False,
                                self._uid,
                                "'%s'" % str(fields.Datetime.to_string(fields.datetime.now())),
                                tables,
                                where_clause))
                self.env.cr.execute(sync_query, where_clause_params)
            one.is_synced = True
        # Invalidate cached contact count
        self.invalidate_cache(["contact_nbr"], dynamic.ids)