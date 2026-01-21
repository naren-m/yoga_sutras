import ClickableWord from './ClickableWord';

interface ClickableTextProps {
  text: string;
  className?: string;
}

/**
 * Renders Sanskrit text with each word being individually clickable.
 * Words are split by spaces and punctuation, preserving Devanagari daṇḍas (।॥).
 */
export default function ClickableText({ text, className = '' }: ClickableTextProps) {
  // Split text into words and separators
  // Devanagari uses spaces, virama (्), and daṇḍa (।) / double daṇḍa (॥) as separators
  // We want to preserve punctuation but make words clickable
  const tokens = tokenizeDevanagari(text);

  return (
    <span className={className}>
      {tokens.map((token, index) => (
        token.isWord ? (
          <ClickableWord key={index} word={token.text} />
        ) : (
          <span key={index}>{token.text}</span>
        )
      ))}
    </span>
  );
}

interface Token {
  text: string;
  isWord: boolean;
}

/**
 * Tokenizes Devanagari text into words and non-word tokens.
 * Handles Sanskrit punctuation (daṇḍa, double daṇḍa) and spaces.
 */
function tokenizeDevanagari(text: string): Token[] {
  const tokens: Token[] = [];

  // Regex to match:
  // - Words: sequences of Devanagari characters (including nukta, virama, and vowel signs)
  // - Non-words: spaces, punctuation, daṇḍas, numbers, etc.
  const wordPattern = /[\u0900-\u097F]+/g;

  let lastIndex = 0;
  let match;

  while ((match = wordPattern.exec(text)) !== null) {
    // Add any non-word text before this word
    if (match.index > lastIndex) {
      tokens.push({
        text: text.slice(lastIndex, match.index),
        isWord: false,
      });
    }

    // Add the word
    tokens.push({
      text: match[0],
      isWord: true,
    });

    lastIndex = match.index + match[0].length;
  }

  // Add any remaining non-word text
  if (lastIndex < text.length) {
    tokens.push({
      text: text.slice(lastIndex),
      isWord: false,
    });
  }

  return tokens;
}
