from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DocumentEntity(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    source = Column(String(255), default="Uploaded Document")
    version = Column(String(50), default="1.0")
    topic = Column(String(255), default="General")
    document_date = Column(String(50), default=datetime.utcnow().strftime("%Y-%m-%d"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="ready")  # ready, processing, error

    chunks = relationship("KnowledgeChunkEntity", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunkEntity(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")

    document = relationship("DocumentEntity", back_populates="chunks")


class InvestigationEntity(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim = Column(Text, nullable=False)
    classification = Column(String(50), nullable=False)  # CURRENT, OUTDATED, CONFLICTING, UNCERTAIN
    explanation = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    recommendation = Column(Text, nullable=False)
    human_verification_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, default="{}")  # stores steps, comparison, etc.

    evidences = relationship("EvidenceEntity", back_populates="investigation", cascade="all, delete-orphan")


class EvidenceEntity(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    investigation_id = Column(Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    chunk_id = Column(Integer, ForeignKey("knowledge_chunks.id", ondelete="SET NULL"), nullable=True)
    evidence_text = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    source = Column(String(255), default="")
    version = Column(String(50), default="")
    date = Column(String(50), default="")
    is_stored_knowledge = Column(Boolean, default=False)

    investigation = relationship("InvestigationEntity", back_populates="evidences")
