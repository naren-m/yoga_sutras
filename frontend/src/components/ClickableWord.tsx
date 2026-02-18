import { useWordSelection } from '../hooks/useWordSelection';

interface ClickableWordProps {
  word: string;
  className?: string;
}

/**
 * A clickable word component that triggers dictionary lookup when clicked.
 * Shows visual hover state to indicate interactivity.
 */
export default function ClickableWord({ word, className = '' }: ClickableWordProps) {
  const { selectWord, selectedWord } = useWordSelection();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Get position for potential tooltip/panel positioning
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    selectWord(word, { x: rect.left + rect.width / 2, y: rect.bottom });
  };

  const isSelected = selectedWord?.word === word;

  return (
    <span
      onClick={handleClick}
      className={`
        cursor-pointer
        transition-all duration-150
        hover:bg-amber-100 hover:text-amber-900
        rounded px-0.5 -mx-0.5
        ${isSelected ? 'bg-amber-200 text-amber-900' : ''}
        ${className}
      `}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const rect = (e.target as HTMLElement).getBoundingClientRect();
          selectWord(word, { x: rect.left + rect.width / 2, y: rect.bottom });
        }
      }}
    >
      {word}
    </span>
  );
}
