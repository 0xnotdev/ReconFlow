from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class ShopifyOrder(Base):
    __tablename__ = 'shopify_orders'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), index=True, nullable=True)
    shopify_id = Column(String, nullable=False, index=True)
    order_number = Column(String)
    total_price = Column(Float)
    subtotal_price = Column(Float)
    total_tax = Column(Float, default=0.0)
    total_discounts = Column(Float, default=0.0)
    financial_status = Column(String)  # paid, refunded, partially_refunded, pending
    fulfillment_status = Column(String)
    customer_email = Column(String)
    customer_name = Column(String)
    gateway = Column(String)           # stripe, paypal, etc
    payment_gateway_names = Column(String)
    refunded_amount = Column(Float, default=0.0)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
    imported_at = Column(DateTime)

    organization = relationship('Organization', back_populates='shopify_orders')
    client = relationship('Client', back_populates='shopify_orders')
