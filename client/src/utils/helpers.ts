const NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"];

export const languageUsesSpaces = (langCode: string) => {
  return !NO_SPACE_LANGUAGES.includes(langCode);
};

export const removeAnnotations = (text: string) => {
  return text.replace(/[\[\(].+?[\]\)]/gu, "").trim();
};

export const removePunctuation = (text: string): string => {
  return text.replace(/\p{P}|\p{S}/gu, "");
}


export const isAnnotation = (text: string) => /^\s*[\[\(].+[\]\)]\s*$/u.test(text);
