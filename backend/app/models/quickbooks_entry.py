from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class QuickBooksEntry(Base):
    __tablename__ = 'quickbooks_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'), index=True, nullable=True)
    qb_id = Column(String, nullable=False, index=True)
    transaction_type = Column(String)  # Payment, Invoice, SalesReceipt, Refund
    doc_number = Column(String)
    amount = Column(Float)
    customer_name = Column(String)
    customer_email = Column(String)
    account_name = Column(String)
    memo = Column(String)
    payment_method = Column(String)
    payment_ref = Column(String)       # reference to stripe charge/PI
    txn_date = Column(DateTime)
    imported_at = Column(DateTime)

    organization = relationship('Organization', back_populates='quickbooks_entries')
    client = relationship('Client', back_populates='quickbooks_entries')
