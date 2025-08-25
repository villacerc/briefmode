from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, func, create_engine
from sqlalchemy.orm import relationship, sessionmaker # for creating database sessions 
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(Text)
    channel_name = Column(Text)
    language_code = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    transcript_snippets = relationship("TranscriptSnippet", back_populates="video", cascade="all, delete-orphan")

class TranscriptSnippet(Base):
    __tablename__ = "transcript_snippets"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    video = relationship("Video", back_populates="transcript_snippets")
    translation_snippets = relationship("TranslationSnippet", back_populates="transcript_snippet", cascade="all, delete-orphan")

class TranslationSnippet(Base):
    __tablename__ = "translation_snippets"

    id = Column(Integer, primary_key=True, index=True)
    snippet_id = Column(Integer, ForeignKey("transcript_snippets.id", ondelete="CASCADE"), nullable=False)
    language_code = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    transcript_snippet = relationship("TranscriptSnippet", back_populates="translation_snippets")

# Database setup
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/briefmode"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)