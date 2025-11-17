export type DictionaryWordEntry = {
  parts_of_speech: PartsOfSpeech[];
  romanized: string;
  phonetic_spelling: string;
  translations: string[];
  word: string;
  source_lang_code: string;
};

export type VideoInfo = {
  source_id: string;
  title: string;
  source_lang_code: string;
}

export type DictionarySnippetEntry = {
  text: string;
  translation: string;
  source_lang_code: string;
  target_lang_code: string;
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
  source_lang_code: string;
  target_lang_code: string;
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