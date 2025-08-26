from sqlalchemy import Index, Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    source_id = Column(String(64), unique=True, nullable=False, index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    title = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    language = relationship("Language", back_populates="videos")
    transcript_snippets = relationship(
        "TranscriptSnippet", 
        back_populates="video", 
        cascade="all, delete-orphan", 
        order_by="TranscriptSnippet.start",
    )

class TranscriptSnippet(Base):
    __tablename__ = "transcript_snippets"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False) # Delete transcript snippets if video is deleted
    text = Column(Text, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    video = relationship("Video", back_populates="transcript_snippets")
    # all: cascades operations like save, update, delete, etc. from the parent
    # delete-orphan: if a translation snippet no longer has a parent TranscriptSnippet, then SQLAlchemy will mark it for deletion automatically.
    translations = relationship("Translation", back_populates="transcript_snippet", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_snippet_videoId_start", "video_id", "start", unique=True),
    )

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey("transcript_snippets.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    transcript_snippet = relationship("TranscriptSnippet", back_populates="translations")
    language = relationship("Language", back_populates="translations")

    __table_args__ = (
        Index("ix_translations_snippet_lang", "snippet_id", "language_id", unique=True),
    )

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    videos = relationship("Video", back_populates="language")
    translations = relationship("Translation", back_populates="language")

