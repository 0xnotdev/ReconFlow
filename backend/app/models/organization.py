from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    stripe_access_token = Column(String, nullable=True)
    stripe_account_id = Column(String, nullable=True)
    shopify_access_token = Column(String, nullable=True)
    shopify_shop_domain = Column(String, nullable=True)
    quickbooks_access_token = Column(String, nullable=True)
    quickbooks_refresh_token = Column(String, nullable=True)
    quickbooks_realm_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship('User', back_populates='organizations')
    stripe_transactions = relationship('StripeTransaction', back_populates='organization')
    shopify_orders = relationship('ShopifyOrder', back_populates='organization')
    quickbooks_entries = relationship('QuickBooksEntry', back_populates='organization')
    discrepancies = relationship('Discrepancy', back_populates='organization')
