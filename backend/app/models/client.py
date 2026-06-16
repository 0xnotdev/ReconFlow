from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Client(Base):
    __tablename__ = 'clients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship('Organization', back_populates='clients')
    stripe_transactions = relationship('StripeTransaction', back_populates='client')
    shopify_orders = relationship('ShopifyOrder', back_populates='client')
    quickbooks_entries = relationship('QuickBooksEntry', back_populates='client')
    discrepancies = relationship('Discrepancy', back_populates='client')
