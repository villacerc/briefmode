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

export const formatSnippetTime = (seconds: number) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};


export const isAnnotation = (text: string) => /^\s*[\[\(].+[\]\)]\s*$/u.test(text);
