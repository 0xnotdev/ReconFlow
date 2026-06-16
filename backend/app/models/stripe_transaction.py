from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class StripeTransaction(Base):
    __tablename__ = 'stripe_transactions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), index=True)
    stripe_id = Column(String, unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)       # in dollars
    currency = Column(String, default='usd')
    status = Column(String)                       # succeeded, failed, refunded
    customer_email = Column(String)
    customer_name = Column(String)
    description = Column(String)
    stripe_fee = Column(Float, default=0.0)
    net_amount = Column(Float)                    # amount - fee
    payment_intent_id = Column(String)
    charge_id = Column(String)
    refunded = Column(Boolean, default=False)
    refund_amount = Column(Float, default=0.0)
    disputed = Column(Boolean, default=False)
    created_at = Column(DateTime)                 # from Stripe
    imported_at = Column(DateTime)

    organization = relationship('Organization', back_populates='stripe_transactions')
