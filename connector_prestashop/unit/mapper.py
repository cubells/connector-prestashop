# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector.unit.mapper import ExportMapper
from openerp.addons.connector.unit.mapper import mapping


class PrestashopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(PrestashopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr) or ''
        if isinstance(from_attr, basestring):
            column = self.model._all_columns[from_attr].column
            if column._type == 'boolean':
                return res and 1 or 0
            elif column._type == 'float':
                res = str(res)
        return res


class TranslationPrestashopExportMapper(PrestashopExportMapper):

    @mapping
    def translatable_fields(self, record):
        fields = getattr(self, '_translatable_fields', [])
        if fields:
            translated_fields = self._convert_languages(
                self._get_record_by_lang(record), fields)
            return translated_fields
        return {}

    def _get_record_by_lang(self, record):
        # get the backend's languages
        languages = self.backend_record.language_ids
        records = {}
        # for each languages:
        for language in languages:
            # get the translated record
            record = record.with_context(
                lang=language['code'])
            # put it in the dict
            records[language['prestashop_id']] = record
        return records

    def _convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for from_attr, to_attr in translatable_fields:
            value = {'language': []}
            for language_id, record in records_by_language.iteritems():
                value['language'].append({
                    'attrs': {'id': str(language_id)},
                    'value': record[from_attr] or ''
                })
            res[to_attr] = value
        return res


@prestashop
class MailMessageMapper(ImportMapper):
    _model_name = 'prestashop.mail.message'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def type(self, record):
        return {'type': 'comment'}

    @mapping
    def object_ref(self, record):
        binder = self.binder_for('prestashop.sale.order')
        order_id = binder.to_odoo(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order_id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.binder_for('prestashop.res.partner')
            partner_id = binder.to_odoo(record['id_customer'], unwrap=True)
            return {'author_id': partner_id}
        return {}


@prestashop
class ProductPricelistMapper(ImportMapper):
    _model_name = 'prestashop.groups.pricelist'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def static(self, record):
        return {'active': True, 'type': 'sale'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    @only_create
    def versions(self, record):
        item = {
            'min_quantity': 0,
            'sequence': 5,
            'base': 1,
            'price_discount': - float(record['reduction']) / 100.0,
        }
        version = {
            'name': 'Version',
            'active': True,
            'items_id': [(0, 0, item)],
        }
        return {'version_id': [(0, 0, version)]}
