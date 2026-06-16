from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum
import enum, uuid
from datetime import datetime
from app.database import Base

class IssueType(str, enum.Enum):
    MISSING_TRANSACTION = 'missing_transaction'
    DUPLICATE_TRANSACTION = 'duplicate_transaction'
    PAYOUT_MISMATCH = 'payout_mismatch'
    REFUND_MISMATCH = 'refund_mismatch'
    CHARGEBACK_MISMATCH = 'chargeback_mismatch'
    FEE_VARIANCE = 'fee_variance'
    REVENUE_LEAK = 'revenue_leak'

class DiscrepancyStatus(str, enum.Enum):
    OPEN = 'open'
    RESOLVED = 'resolved'
    IGNORED = 'ignored'

class Discrepancy(Base):
    __tablename__ = 'discrepancies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), index=True, nullable=True)
    issue_type = Column(SAEnum(IssueType), nullable=False)
    status = Column(SAEnum(DiscrepancyStatus), default=DiscrepancyStatus.OPEN)
    amount = Column(Float)
    financial_impact = Column(Float, default=0.0)
    recoverable_amount = Column(Float, default=0.0)
    recovery_probability = Column(Float, default=0.0)
    customer_name = Column(String)
    customer_email = Column(String)
    date = Column(DateTime)
    stripe_ref = Column(String, nullable=True)   # stripe transaction id
    shopify_ref = Column(String, nullable=True)  # shopify order id
    qb_ref = Column(String, nullable=True)       # quickbooks entry id
    confidence_score = Column(Float)             # 0.0 to 1.0
    suggested_cause = Column(String)
    what_happened = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship('Organization', back_populates='discrepancies')
    client = relationship('Client', back_populates='discrepancies')
