# This file is part of the contract_payment_type module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from trytond.pyson import Eval, Bool

__all__ = ['Contract', 'ContractConsumption']
__metaclass__ = PoolMeta


class Contract:
    __name__ = 'contract'
    company_party = fields.Function(fields.Many2One('party.party',
            'Company Party'), 'get_company_party')
    payment_type = fields.Many2One('account.payment.type',
        'Payment Type', domain=[
            ('kind', '=', 'receivable'),
            ])
    receivable_bank_account = fields.Many2One('bank.account',
        'Receivable Bank Account', domain=[
            ('owners', '=', Eval('party')),
        ], states={
            'invisible': ~Bool(Eval('payment_type')),
        }, depends=['company_party'],
        help='Party bank account')
    company_bank_account = fields.Many2One('bank.account',
        'Company Bank Account',
        domain=[
            ('owners', '=', Eval('company_party')),
        ], states={
            'invisible': ~Bool(Eval('payment_type')),
        }, depends=['id', 'payment_type'],
        help='Default party payable bank account')

    def get_company_party(self, name=None):
        return self.company.party.id if self.company else None


class ContractConsumption:
    __name__ = 'contract.consumption'

    @classmethod
    def _get_invoice(cls, keys):
        invoice = super(ContractConsumption, cls)._get_invoice(keys)

        values = dict(keys)
        contract = values['contract']

        if contract.payment_type:
            invoice.payment_type = contract.payment_type

            if invoice.payment_type.account_bank == 'party':
                if contract.receivable_bank_account:
                    invoice.bank_account = contract.receivable_bank_account
            elif invoice.payment_type.account_bank == 'company':
                if contract.company_bank_account:
                    invoice.bank_account = contract.company_bank_account

        return invoice