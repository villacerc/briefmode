from sqlalchemy import CheckConstraint, UniqueConstraint, Index, Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import enum

class SnippetType(enum.Enum):
    TRANSCRIPT = "transcript"
    POS_EXAMPLE = "pos_example"

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    source_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(Text)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    language = relationship("Language", back_populates="videos")
    transcript_snippets = relationship(
        "TranscriptSnippet", 
        back_populates="video", 
        lazy="selectin",
        cascade="all, delete-orphan", 
        order_by="TranscriptSnippet.start",
    )

class TranscriptSnippet(Base):
    __tablename__ = "transcript_snippets"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    video = relationship("Video", back_populates="transcript_snippets")
    snippet = relationship("Snippet", back_populates="transcript_snippets")
    snippet_words = relationship("SnippetWord", back_populates="transcript_snippet", cascade="all, delete-orphan", lazy="selectin", order_by="SnippetWord.order_index")

    __table_args__ = (
        Index("ix_snippet_videoId_start", "video_id", "start", unique=True),
    )

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False, unique=True, index=True)

    created_at = Column(DateTime, server_default=func.now())
    
    snippet_words = relationship("SnippetWord", back_populates="snippet", cascade="all, delete-orphan", lazy="selectin", order_by="SnippetWord.order_index")
    translations = relationship("SnippetTranslation", back_populates="snippet", cascade="all, delete-orphan")
    transcript_snippets = relationship("TranscriptSnippet", back_populates="snippet", cascade="all, delete-orphan")
    dictionary_pos_list = relationship("DictionaryPOS", back_populates="snippet", cascade="all, delete-orphan")

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
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    snippet_id = Column(Integer, ForeignKey("snippets.id"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    
    language = relationship("Language", back_populates="dictionary_pos_list")
    snippet = relationship("Snippet", back_populates="dictionary_pos_list", lazy="selectin")
    word = relationship("Word", back_populates="dictionary_pos_list")

    __table_args__ = (
        UniqueConstraint("word_id", "name", name="uq_word_pos_name"),
        Index("ix_dictionary_pos_word_lang", "word_id", "language_id"),
    )

class SnippetWord(Base):
    __tablename__ = "snippet_words"

    id = Column(Integer, primary_key=True)

    # Optional relationships
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"), nullable=True)
    transcript_snippet_id = Column(Integer, ForeignKey("transcript_snippets.id", ondelete="CASCADE"), nullable=True)

    word_id = Column(Integer, ForeignKey("words.id", ondelete="SET NULL"))
    part_of_speech_tag = Column(String(50))
    text = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    transcript_snippet = relationship("TranscriptSnippet", back_populates="snippet_words")
    snippet = relationship("Snippet", back_populates="snippet_words")
    word = relationship("Word", back_populates="snippet_words", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            """
            (snippet_id IS NOT NULL AND transcript_snippet_id IS NULL)
            OR (snippet_id IS NULL AND transcript_snippet_id IS NOT NULL)
            """,
            name="check_one_fk_not_null"
        ),
    )

class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(String(255), nullable=False)
    romanized = Column(String(255))
    phonetic_spelling = Column(String(255))
    tts_audio = Column(Text)

    created_at = Column(DateTime, server_default=func.now())

    language = relationship("Language", back_populates="words")
    snippet_words = relationship("SnippetWord", back_populates="word")
    word_translations = relationship("WordTranslation", back_populates="word", cascade="all, delete-orphan")
    dictionary_pos_list = relationship("DictionaryPOS", back_populates="word", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_word_text_lang", "text", "language_id", unique=True),
    )

class WordTranslation(Base):
    __tablename__ = "word_translations"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    text = Column(Text, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    word = relationship("Word", back_populates="word_translations")
    language = relationship("Language", back_populates="word_translations")

    __table_args__ = (
        Index("ix_translation_word_lang", "word_id", "language_id"),
        UniqueConstraint("word_id", "language_id", "text", name="uq_translation_word_lang_text"),
    )

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    bcp47_code = Column(String(20), unique=True, nullable=False, index=True)

    created_at = Column(DateTime, server_default=func.now())

    dictionary_pos_list = relationship("DictionaryPOS", back_populates="language")
    snippet_translations = relationship("SnippetTranslation", back_populates="language")
    words = relationship("Word", back_populates="language")
    word_translations = relationship("WordTranslation", back_populates="language")
    videos = relationship("Video", back_populates="language")
