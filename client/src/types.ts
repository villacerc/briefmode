export type DictionaryWordEntry = {
  parts_of_speech: PartsOfSpeech[];
  romanized: string;
  phonetic_spelling: string;
  translations: string[];
  word: string;
};

export type DictionarySnippetEntry = {
  text: string;
  translation: string;
  source_language: string;
  target_language: string;
  snippet_words: SnippetWord[];
}

export type PartsOfSpeech = {
  definition: string;
  example_words: SnippetWord[];
  example_translation: string;
  name: string;
}

export type TranslatedSnippet = {
  snippet_id: number;
  text: string;
  translation: string
  transcript_language: string;
  translation_language: string;
  start: number;
  end: number;
  duration: number;
  snippet_words: SnippetWord[];
};

export type SnippetWord = {
  text: string;
  part_of_speech: string;
  romanized: string;
  order_index: number;
  translations: Translation[];
}

export type Translation = {
  text: string;
}