from sqlalchemy import UniqueConstraint, Index, Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    source_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(Text)

    created_at = Column(DateTime, server_default=func.now())

    transcript_snippets = relationship(
        "TranscriptSnippet", 
        back_populates="video", 
        cascade="all, delete-orphan", 
        order_by="TranscriptSnippet.start",
    )

class TranscriptSnippet(Base):
    __tablename__ = "transcript_snippets"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=False, unique=True)
    text = Column(Text, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    video = relationship("Video", back_populates="transcript_snippets")
    snippet = relationship("Snippet", back_populates="transcript_snippet")

    __table_args__ = (
        Index("ix_snippet_videoId_start", "video_id", "start", unique=True),
    )

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    language = relationship("Language", back_populates="snippets")
    snippet_words = relationship("SnippetWord", back_populates="snippet", cascade="all, delete-orphan")
    translations = relationship("SnippetTranslation", back_populates="snippet", cascade="all, delete-orphan")
    transcript_snippet = relationship(
        "TranscriptSnippet",
        back_populates="snippet",
        uselist=False, # one-to-one relationship
        cascade="all, delete-orphan",
    )
    pos_example = relationship("DictionaryPOS", back_populates="normalized_example", uselist=False)

    __table_args__ = (
        Index("ix_snippet_text_lang", "text", "language_id"),
    )

class SnippetTranslation(Base):
    __tablename__ = "snippet_translations"

    id = Column(Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    snippet = relationship("Snippet", back_populates="translations")
    language = relationship("Language", back_populates="snippet_translations")

    __table_args__ = (
        Index("ix_snippet_translations_snippet_lang", "snippet_id", "language_id", unique=True),
    )

class DictionaryPOS(Base):
    __tablename__ = "dictionary_pos"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True)
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    example = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    normalized_example = relationship("Snippet", back_populates="pos_example", uselist=False)
    word = relationship("Word", back_populates="pos_examples")

class SnippetWord(Base):
    __tablename__ = "snippet_words"

    id = Column(Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="SET NULL"))
    part_of_speech_tag = Column(String(50))
    text = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    snippet = relationship("Snippet", back_populates="snippet_words")
    word = relationship("Word", back_populates="snippet_words")

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(String(255), nullable=False)
    romanized = Column(String(255))

    created_at = Column(DateTime, server_default=func.now())

    language = relationship("Language", back_populates="words")
    snippet_words = relationship("SnippetWord", back_populates="word")
    translations = relationship("Translation", back_populates="word", cascade="all, delete-orphan")
    pos_examples = relationship("DictionaryPOS", back_populates="word", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_word_text_lang", "text", "language_id", unique=True),
    )

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(Text, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    word = relationship("Word", back_populates="translations")
    language = relationship("Language", back_populates="translations")

    __table_args__ = (
        Index("ix_translation_word_lang", "word_id", "language_id"),
    )
    __table_args__ = (
        UniqueConstraint("word_id", "language_id", "text", name="uq_translation_word_lang_text"),
    )

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    snippets = relationship("Snippet", back_populates="language")
    snippet_translations = relationship("SnippetTranslation", back_populates="language")
    words = relationship("Word", back_populates="language")
    translations = relationship("Translation", back_populates="language")
