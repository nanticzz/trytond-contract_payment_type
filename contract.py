# This file is part of the contract_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import fields

__all__ = ['Contract', 'ContractConsumption']


class Contract(metaclass=PoolMeta):
    __name__ = 'contract'
    payment_type = fields.Many2One('account.payment.type',
        'Payment Type', domain=[
            ('kind', '=', 'receivable'),
        ])

    @staticmethod
    def default_payment_type():
        Config = Pool().get('contract.configuration')
        config = Config(1)
        return config.payment_type.id if config.payment_type else None


class ContractConsumption(metaclass=PoolMeta):
    __name__ = 'contract.consumption'

    @classmethod
    def _group_invoice_key(cls, line):
        grouping = super(ContractConsumption, cls)._group_invoice_key(line)

        consumption_id, _ = line
        consumption = cls(consumption_id)
        grouping.append(
            ('payment_type', consumption.contract_line.contract.payment_type))
        return grouping

    @classmethod
    def _invoice(cls, consumptions):
        Invoice = Pool().get('account.invoice')

        invoices = super(ContractConsumption, cls)._invoice(consumptions)

        to_write = []
        for invoice in invoices:
            contract = None
            for line in invoice.lines:
                if line.origin and line.origin.__name__ == 'contract.consumption':
                    contract = line.origin.contract_line.contract
                    break
            if contract:
                payment_type = (contract.payment_type or
                    contract.party.customer_payment_type)
                if payment_type:
                    values = {}
                    values['payment_type'] = payment_type
                    if hasattr(invoice, 'bank_account'):
                        invoice.payment_type = payment_type
                        invoice._get_bank_account()
                        values['bank_account'] = (invoice.bank_account
                            if invoice.bank_account else None)
                    to_write.extend(([invoice], values))

        if to_write:
            Invoice.write(*to_write)

        return invoices
