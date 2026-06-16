from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.stripe_transaction import StripeTransaction
from app.models.shopify_order import ShopifyOrder
from app.models.quickbooks_entry import QuickBooksEntry
from app.models.discrepancy import Discrepancy, IssueType, DiscrepancyStatus
from datetime import datetime, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)

TOLERANCE = 0.02           # 2 cent tolerance for float comparison
DATE_WINDOW_DAYS = 3       # transactions within 3 days considered same-period
EXPECTED_STRIPE_RATE = 0.029   # 2.9%
EXPECTED_STRIPE_FLAT = 0.30    # $0.30 per transaction

class ReconciliationEngine:
    def __init__(self, org_id: str, db: Session):
        self.org_id = org_id
        self.db = db
        self.discrepancies: List[Discrepancy] = []

    def run(self) -> dict:
        '''Run all detection passes. Returns summary dict.'''
        logger.info(f'Starting reconciliation for org {self.org_id}')
        # Clear old open discrepancies before re-running
        self.db.query(Discrepancy).filter(
            and_(Discrepancy.org_id == self.org_id, Discrepancy.status == DiscrepancyStatus.OPEN)
        ).delete()
        self.db.commit()

        stripe_txns = self.db.query(StripeTransaction).filter(
            StripeTransaction.org_id == self.org_id
        ).all()
        qb_entries = self.db.query(QuickBooksEntry).filter(
            QuickBooksEntry.org_id == self.org_id
        ).all()
        shopify_orders = self.db.query(ShopifyOrder).filter(
            ShopifyOrder.org_id == self.org_id
        ).all()

        self._detect_missing_in_qb(stripe_txns, qb_entries)
        self._detect_duplicate_qb(qb_entries)
        self._detect_refund_mismatch(stripe_txns, qb_entries)
        self._detect_chargeback_mismatch(stripe_txns, qb_entries)
        self._detect_fee_variance(stripe_txns)
        self._detect_revenue_leak(shopify_orders, stripe_txns)

        for d in self.discrepancies:
            self.db.add(d)
        self.db.commit()

        total_at_risk = sum(d.amount or 0 for d in self.discrepancies)
        total_reconciled = sum(t.amount for t in stripe_txns if t.status == 'succeeded')
        return {
            'discrepancies_found': len(self.discrepancies),
            'total_at_risk': round(total_at_risk, 2),
            'total_reconciled': round(total_reconciled, 2),
        }

    def _detect_missing_in_qb(self, stripe_txns, qb_entries):
        '''Detection 1: Stripe charge has no matching QB entry'''
        qb_amounts = {}
        for e in qb_entries:
            key = round(e.amount, 2)
            if key not in qb_amounts: qb_amounts[key] = []
            qb_amounts[key].append(e)

        for txn in stripe_txns:
            if txn.status != 'succeeded': continue
            net_key = round(txn.net_amount or txn.amount, 2)
            # Try to find a QB entry close in amount and date
            candidates = qb_amounts.get(net_key, []) + qb_amounts.get(round(txn.amount, 2), [])
            matched = False
            for candidate in candidates:
                if abs((candidate.txn_date - txn.created_at).days) <= DATE_WINDOW_DAYS:
                    matched = True
                    break
            if not matched:
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.MISSING_TRANSACTION,
                    amount=txn.amount,
                    financial_impact=txn.amount,
                    recoverable_amount=txn.amount,
                    recovery_probability=0.90,
                    customer_name=txn.customer_name,
                    customer_email=txn.customer_email,
                    date=txn.created_at,
                    stripe_ref=txn.stripe_id,
                    confidence_score=0.85,
                    suggested_cause='Stripe charge found but no matching QuickBooks payment entry detected.'
                ))

    def _detect_duplicate_qb(self, qb_entries):
        '''Detection 2: Same amount + same date in QB more than once'''
        seen = {}
        for e in qb_entries:
            key = (round(e.amount, 2), e.txn_date.date() if e.txn_date else None, e.customer_name)
            if key in seen:
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.DUPLICATE_TRANSACTION,
                    amount=e.amount,
                    financial_impact=e.amount,
                    recoverable_amount=e.amount,
                    recovery_probability=1.0,
                    customer_name=e.customer_name,
                    date=e.txn_date,
                    qb_ref=e.qb_id,
                    confidence_score=0.90,
                    suggested_cause=f'Duplicate entry detected in QuickBooks. Same amount and date as entry {seen[key]}.'
                ))
            else:
                seen[key] = e.qb_id

    def _detect_refund_mismatch(self, stripe_txns, qb_entries):
        '''Detection 4: Stripe shows refund but no QB refund entry'''
        qb_refunds = [e for e in qb_entries if e.transaction_type in ('Refund', 'CreditMemo')]
        qb_refund_amounts = [round(e.amount, 2) for e in qb_refunds]

        for txn in stripe_txns:
            if not txn.refunded or txn.refund_amount <= 0: continue
            refund_key = round(txn.refund_amount, 2)
            if refund_key not in qb_refund_amounts:
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.REFUND_MISMATCH,
                    amount=txn.refund_amount,
                    financial_impact=txn.refund_amount,
                    recoverable_amount=0.0,
                    recovery_probability=0.0,
                    customer_name=txn.customer_name,
                    date=txn.created_at,
                    stripe_ref=txn.stripe_id,
                    confidence_score=0.92,
                    suggested_cause='Refund recorded in Stripe but no corresponding refund/credit memo found in QuickBooks.'
                ))

    def _detect_chargeback_mismatch(self, stripe_txns, qb_entries):
        '''Detection 5: Stripe shows dispute but QB has no adjustment'''
        for txn in stripe_txns:
            if not txn.disputed: continue
            # Look for QB entry that references this dispute
            found = any(
                e for e in qb_entries
                if e.transaction_type == 'JournalEntry'
                and e.txn_date
                and abs((e.txn_date - txn.created_at).days) <= 30
                and abs(e.amount - txn.amount) < TOLERANCE
            )
            if not found:
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.CHARGEBACK_MISMATCH,
                    amount=txn.amount,
                    financial_impact=txn.amount,
                    recoverable_amount=0.0,
                    recovery_probability=0.0,
                    customer_name=txn.customer_name,
                    date=txn.created_at,
                    stripe_ref=txn.stripe_id,
                    confidence_score=0.88,
                    suggested_cause='Chargeback/dispute found in Stripe but no corresponding adjustment in QuickBooks. Revenue may be overstated.'
                ))

    def _detect_fee_variance(self, stripe_txns):
        '''Detection 6: Actual Stripe fee differs from expected'''
        for txn in stripe_txns:
            if txn.status != 'succeeded': continue
            if not txn.stripe_fee or txn.stripe_fee == 0: continue
            expected_fee = round(txn.amount * EXPECTED_STRIPE_RATE + EXPECTED_STRIPE_FLAT, 2)
            actual_fee = round(txn.stripe_fee, 2)
            variance = abs(actual_fee - expected_fee)
            if variance > 0.10:  # more than 10 cent variance
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.FEE_VARIANCE,
                    amount=variance,
                    financial_impact=variance,
                    recoverable_amount=variance,
                    recovery_probability=1.0,
                    customer_name=txn.customer_name,
                    date=txn.created_at,
                    stripe_ref=txn.stripe_id,
                    confidence_score=0.75,
                    suggested_cause=f'Expected Stripe fee ${expected_fee:.2f}, actual ${actual_fee:.2f}. Variance of ${variance:.2f}.'
                ))

    def _detect_revenue_leak(self, shopify_orders, stripe_txns):
        '''Detection 7: Shopify order paid but no Stripe charge found'''
        stripe_amounts = {}
        for t in stripe_txns:
            if t.status != 'succeeded': continue
            key = round(t.amount, 2)
            if key not in stripe_amounts: stripe_amounts[key] = []
            stripe_amounts[key].append(t)

        for order in shopify_orders:
            if order.financial_status != 'paid': continue
            if order.gateway not in ('stripe', 'stripe_cc'): continue
            amt_key = round(order.total_price, 2)
            candidates = stripe_amounts.get(amt_key, [])
            matched = any(
                t for t in candidates
                if abs((t.created_at - order.created_at).days) <= DATE_WINDOW_DAYS
            )
            if not matched:
                self.discrepancies.append(Discrepancy(
                    org_id=self.org_id,
                    issue_type=IssueType.REVENUE_LEAK,
                    amount=order.total_price,
                    financial_impact=order.total_price,
                    recoverable_amount=order.total_price,
                    recovery_probability=0.80,
                    customer_name=order.customer_name,
                    customer_email=order.customer_email,
                    date=order.created_at,
                    shopify_ref=order.shopify_id,
                    confidence_score=0.80,
                    suggested_cause='Shopify order marked as paid via Stripe but no matching Stripe charge found. Potential revenue leak.'
                ))
