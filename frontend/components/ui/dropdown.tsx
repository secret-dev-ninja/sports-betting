import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DropdownOption {
  value: string;
  label: string;
}

interface SearchableDropdownProps {
  options: DropdownOption[];
  placeholder: string;
  onSelect: (value: string) => void;
  viewCount?: number; // New prop to set visible item count
}

const SearchableDropdown: React.FC<SearchableDropdownProps> = ({
  options,
  placeholder,
  onSelect,
  viewCount,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLabel, setSelectedLabel] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Limit the number of options shown based on `viewCount` or show all filtered options
  const visibleOptions = viewCount ? filteredOptions.slice(0, viewCount) : filteredOptions;

  const handleSelect = (option: DropdownOption) => {
    setSelectedLabel(option.label); // Show the label in the button
    onSelect(option.value); // Pass the value to the parent
    setIsOpen(false); // Close the dropdown
    setSearchTerm(''); // Clear the search term
  };

  const handleClose = () => {
    setIsOpen(false);
    setSearchTerm('');
  };

  // Close dropdown on ESC key or outside click
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleClose();
      }
    };

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        handleClose();
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
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full px-4 py-2 border rounded-lg shadow-sm text-left transition duration-200 ${
          isOpen ? 'border-blue-500 ring-2 ring-blue-300' : 'border-gray-300'
        } bg-white hover:shadow-md`}
      >
        {selectedLabel || placeholder}
        <span
          className={`float-right transform transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        >
          ▼
        </span>
      </button>

      {/* Dropdown Content */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute mt-2 w-full bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto z-10"
          >
            {/* Search Input */}
            <div className="p-2 border-b border-gray-200">
              <input
                type="text"
                className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-400 focus:outline-none"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Options List */}
            <div className="py-2">
              {visibleOptions.length > 0 ? (
                visibleOptions.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelect(option)}
                    className="block w-full px-4 py-2 text-left text-gray-700 hover:bg-blue-100 hover:text-blue-700 transition duration-200"
                  >
                    {option.label}
                  </button>
                ))
              ) : (
                <div className="p-4 text-gray-500 text-center">
                  No results found
                </div>
              )}

              {/* Message to indicate more options are available */}
              {viewCount && filteredOptions.length > viewCount && (
                <div className="px-4 py-2 text-sm text-gray-500 text-center">
                  Showing {viewCount} of {filteredOptions.length} results. Search to view more.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SearchableDropdown;
