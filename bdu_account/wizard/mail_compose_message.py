# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, SUPERUSER_ID, tools

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'


    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """ - mass_mailing: we cannot render, so return the template values
            - normal mode: return rendered values
            /!\ for x2many field, this onchange return command instead of ids
        """

        if 'default_model' in self.env.context and self.env.context['default_model'] == 'sale.order' and template_id and composition_mode != 'mass_mail':

            values = self.generate_email_for_composer(template_id, [res_id])[res_id]
            # transform attachments into attachment_ids; not attached to the document because this will
            # be done further in the posting process, allowing to clean database if email not send
            Attachment = self.env['ir.attachment']
            res_id = int(self.env.context['default_res_id'])
            sale = self.env['sale.order'].browse(res_id)
            rept_name = 'quotation'
            if sale.state in ['sale','done']:
                rept_name = 'sale'

            attachobj = Attachment.search([('res_model','=','sale.order'),('res_id','=',res_id),('name','ilike',rept_name)])
            if attachobj:
                values.setdefault('attachment_ids', list()).append(attachobj[0].id)
            else:
                for attach_fname, attach_datas in values.pop('attachments', []):
                    data_attach = {
                        'name': attach_fname,
                        'datas': attach_datas,
                        'datas_fname': attach_fname,
                        'res_model': 'mail.compose.message',
                        'res_id': 0,
                        'type': 'binary',  # override default_type from context, possibly meant for another model!
                    }
                    values.setdefault('attachment_ids', list()).append(Attachment.create(data_attach).id)
            if values.get('body_html'):
                values['body'] = values.pop('body_html')

            # This onchange should return command instead of ids for x2many field.
            # ORM handle the assignation of command list on new onchange (api.v8),
            # this force the complete replacement of x2many field with
            # command and is compatible with onchange api.v7
            values = self._convert_to_write(values)

            return {'value': values}
        else:
            return super(MailComposer, self).onchange_template_id(template_id, composition_mode, model, res_id)


        