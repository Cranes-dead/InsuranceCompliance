from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), default="policy")
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    status = Column(String(20), default="uploaded")
    
    # Relationship
    compliance_results = relationship("ComplianceResult", back_populates="document")

class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    classification = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    violations = Column(Text)
    recommendations = Column(Text)
    explanation = Column(Text)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    document = relationship("Document", back_populates="compliance_results")

class IRDAIGuideline(Base):
    __tablename__ = "irdai_guidelines"
    
    id = Column(Integer, primary_key=True, index=True)
    guideline_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))
    effective_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String(500))

# Database setup function
def create_database(database_url: str):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine

def get_session_maker(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)