import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface InputOption {
  value: number;
  label: string;
}

interface SearchableInputProps {
  options: InputOption[];
  placeholder: string;
  onSelect: (value: InputOption) => void;
  viewCount?: number;
}

const SearchableInput: React.FC<SearchableInputProps> = ({
  options,
  placeholder,
  onSelect,
  viewCount,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const visibleOptions = viewCount ? filteredOptions.slice(0, viewCount) : filteredOptions;

  const handleSelect = (option: InputOption) => {
    onSelect(option);
    setIsOpen(false);
    setSearchTerm(option.label);
  };

  const highlightMatch = (text: string, search: string) => {
    if (!search) return text;
    const regex = new RegExp(`(${search})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) => 
      regex.test(part) ? <strong key={i}>{part}</strong> : part
    );
  };

  // Close dropdown on ESC key or outside click
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative inline-block w-64" ref={dropdownRef}>
      <input
        type="text"
        className="w-full px-4 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-400 focus:outline-none"
        placeholder={placeholder}
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setIsOpen(true);
        }}
        onClick={() => {
          setIsOpen(true);
          setSearchTerm('');
        }}
      />

      <AnimatePresence>
        {isOpen && searchTerm && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute mt-2 w-full bg-white border rounded-lg shadow-lg max-h-80 overflow-y-auto z-10"
          >
            <div className="py-2">
              {visibleOptions.length > 0 ? (
                visibleOptions.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelect(option)}
                    className="block w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-100 hover:text-blue-700 transition duration-200"
                  >
                    {highlightMatch(option.label, searchTerm)}
                  </button>
                ))
              ) : (
                <div className="p-4 text-gray-500 text-center">
                  No results found
                </div>
              )}

              {viewCount && filteredOptions.length > viewCount && (
                <div className="px-4 py-2 text-sm text-gray-500 text-center">
                  Showing {viewCount} of {filteredOptions.length} results. Type to view more.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SearchableInput;