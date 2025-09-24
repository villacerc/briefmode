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
  romanized: string;
  order_index: number;
  translations: Translation[];
}

export type Translation = {
  text: string;
  order_index: number;
}