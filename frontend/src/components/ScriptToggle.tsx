import { useState, useRef, useEffect } from 'react';
import { useScriptPreference } from '../hooks/useScriptPreference';
import type { ScriptPreference } from '../contexts/scriptPreferenceTypes';

const OPTIONS: { value: ScriptPreference; label: string; description: string }[] = [
  { value: 'both', label: 'Both', description: 'Devanagari + IAST' },
  { value: 'devanagari', label: 'देवनागरी', description: 'Devanagari only' },
  { value: 'iast', label: 'IAST', description: 'Roman transliteration' },
];

/**
 * Dropdown toggle for script display preference.
 * Accessible from the header, persists to localStorage.
 */
export default function ScriptToggle() {
  const { preference, setPreference } = useScriptPreference();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  const currentOption = OPTIONS.find((opt) => opt.value === preference) ?? OPTIONS[0];

  const handleSelect = (value: ScriptPreference) => {
    setPreference(value);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-amber-700/50 hover:bg-amber-700 rounded-lg text-amber-100 text-sm transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label="Script display preference"
      >
        {/* Settings icon */}
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="hidden sm:inline">{currentOption.label}</span>
        {/* Chevron */}
        <svg
          className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-amber-200 z-50 overflow-hidden"
          role="listbox"
          aria-label="Select script preference"
        >
          <div className="p-2 border-b border-amber-100 bg-amber-50">
            <p className="text-xs font-medium text-amber-800 uppercase tracking-wide">Script Display</p>
          </div>
          <div className="py-1">
            {OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={`w-full text-left px-4 py-2 flex items-center justify-between hover:bg-amber-50 transition-colors ${
                  preference === option.value ? 'bg-amber-100' : ''
                }`}
                role="option"
                aria-selected={preference === option.value}
              >
                <div>
                  <p className={`text-sm font-medium ${preference === option.value ? 'text-amber-800' : 'text-gray-700'}`}>
                    {option.label}
                  </p>
                  <p className="text-xs text-gray-500">{option.description}</p>
                </div>
                {preference === option.value && (
                  <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
