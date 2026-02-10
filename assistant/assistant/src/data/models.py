from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from src.data.database import Base

class RegulatoryText(Base):
    """Model for storing regulatory texts."""
    
    __tablename__ = "regulatory_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)  # e.g., "PRA Rulebook"
    section = Column(String(200), nullable=False)  # e.g., "Own Funds"
    paragraph_id = Column(String(50), unique=True, index=True)  # e.g., "PRA_RB_4.2.1"
    content = Column(Text, nullable=False)
    template_reference = Column(String(50), index=True)  # e.g., "C_01.00"
    field_references = Column(JSON)  # List of field IDs this applies to
    effective_date = Column(DateTime)
    validation_rules = Column(JSON)  # List of validation rules
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RegulatoryText(id={self.id}, paragraph_id={self.paragraph_id}, template={self.template_reference})>"