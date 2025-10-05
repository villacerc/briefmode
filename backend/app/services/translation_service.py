# app/services/translation_service.py
from models import TranscriptSnippet, Language, Word, Translation, Video, SnippetWord
from app.stores import TranslationStore, VideoStore
from .json_validators import validate_translation_json
from .helpers import fetch_ai_data
from typing import List, Dict

class TranslationService:
    SEMAPHORE_CONCURRENCY = 10

    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.video_store = VideoStore(db)

    async def get_translations(self, ts_snippets: List[TranscriptSnippet], translation_lang: Language) -> List[Dict]:
        # Create a semaphore to limit concurrency to avoid overloading API and database
        semaphore = asyncio.Semaphore(self.SEMAPHORE_CONCURRENCY)

        async def worker(ts_snippet: TranscriptSnippet, translation_lang: Language):
            async with semaphore:
                translated_snippet = await self.get_translated_snippet(ts_snippet, translation_lang)
                return translated_snippet

        try:
            # Return a list of all translated snippets in same order
            # * unpacks the iterable into individual arguments for a function.
            # eg. (worker(a), worker(b), worker(c))
            return await asyncio.gather(*(worker(s, translation_lang) for s in ts_snippets))
        except Exception as e:
            raise RuntimeError(f"Error occurred while translating snippets. {e}")

    async def get_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language):
        if self.ts_snippet_has_translation_for_language(ts_snippet.snippet_id, translation_lang.id):
            video = self.video_store.get_video(ts_snippet.video_id)
            return self.get_normalized_translated_snippet(ts_snippet, translation_lang, video)

        # Call AI, parse JSON, etc.
        parsed_json = await self.fetch_ai_snippet_translation(ts_snippet.snippet.text, translation_lang)

        # Save to DB
        self.translation_store.save_snippet_translation(ts_snippet.snippet, translation_lang, parsed_json)

        video = self.video_store.get_video(ts_snippet.video_id)
        return self.get_normalized_translated_snippet(ts_snippet, translation_lang, video)

    def ts_snippet_has_translation_for_language(self, snippet_id: int, lang_id: int) -> bool:
        translation = self.translation_store.get_snippet_translation_by_language(snippet_id, lang_id)
        return translation is not None

    async def fetch_ai_snippet_translation(self, snippet_text, translation_lang):
        try:
            prompt = f"""
                   Translate the input below to {translation_lang.name}.
                    Rules:
                    1. Respond ONLY with valid JSON. Do NOT include explanations, comments, or extra text.
                    2. Capitalize the first word only if required by grammar.
                    3. Break down input into individual words or tokens, including:
                       - "word": original word
                       - "part_of_speech": only include the **main POS label** (e.g., "verb"), not long explanations.
                       - "romanized": Latin script romanization
                       - "translations": at least three translation candidates if possible.
                    4. "romanized" must never contain non-Latin characters.
                    5. Use properly formatted JSON, double quotes, no trailing commas.

                    Output JSON format:

                    {{
                      "snippet_text": "<original input text>",
                      "translation": "<full translated sentence here>",
                      "word_parts": [
                        {{
                          "word": "<original word>",
                          "part_of_speech": "<part of speech>",
                          "romanized": "<romanized form in Latin>",
                          "translations": "<a list of at least three translation candidates if possible>"
                        }}
                      ]
                    }}

                    Input:
                    {snippet_text}
                    """
            parsed_json = await fetch_ai_data(prompt, validate_translation_json)
            return parsed_json
        except Exception as e:
            raise RuntimeError(f"Error fetching AI snippet translation for '{snippet_text}'. {e}")

    def get_normalized_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language, video: Video) -> Dict:
        try:
            snippet_words = ts_snippet.snippet.snippet_words

            snippet_translation = self.translation_store.get_snippet_translation_by_language(ts_snippet.snippet_id, translation_lang.id)

            normalized_snippet_words = [{
                "text": w.text,
                "part_of_speech": w.part_of_speech_tag,
                "romanized": w.word.romanized,
                "translations": [{"text": t.text} for t in w.word.translations],
                "order_index": w.order_index
            } for w in snippet_words]

            return {
                "snippet_id": ts_snippet.id,
                "text": ts_snippet.text,
                "translation": snippet_translation.text if snippet_translation else "",
                "transcript_language": ts_snippet.snippet.language.code,
                "translation_language": translation_lang.code,
                "start": ts_snippet.start,
                "end": ts_snippet.end,
                "duration": ts_snippet.duration,
                "snippet_words": normalized_snippet_words
            }
        except Exception as e:
            raise RuntimeError(f"Error normalizing translated snippet. {e}") from e
