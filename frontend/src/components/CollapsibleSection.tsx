import { useState, useRef, useEffect } from 'react';
import type { ReactNode } from 'react';

interface CollapsibleSectionProps {
  title: string;
  subtitle?: string;
  icon: ReactNode;
  iconColor?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}

/**
 * Collapsible section wrapper with smooth height animation.
 * Used for progressive disclosure in the dictionary panel.
 */
export default function CollapsibleSection({
  title,
  subtitle,
  icon,
  iconColor = 'text-amber-600',
  defaultOpen = true,
  children,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | 'auto'>('auto');

  // Measure content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      const contentHeight = contentRef.current.scrollHeight;
      setHeight(isOpen ? contentHeight : 0);
    }
  }, [isOpen, children]);

  // Update height when children change (e.g., data loads)
  useEffect(() => {
    if (isOpen && contentRef.current) {
      const observer = new ResizeObserver(() => {
        if (contentRef.current) {
          setHeight(contentRef.current.scrollHeight);
        }
      });
      observer.observe(contentRef.current);
      return () => observer.disconnect();
    }
  }, [isOpen]);

  return (
    <section className="mb-3">
      {/* Header - clickable to toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-2 px-1 hover:bg-gray-50 rounded transition-colors group"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2">
          <span className={iconColor}>{icon}</span>
          <div className="text-left">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-gray-400">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Chevron indicator */}
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content with height animation */}
      <div
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
        className="overflow-hidden transition-[height] duration-200 ease-out"
      >
        <div ref={contentRef} className="pt-2 pb-3">
          {children}
        </div>
      </div>
    </section>
  );
}
