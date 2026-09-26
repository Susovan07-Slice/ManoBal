'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Check, X } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface SearchableSelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options?: string[];
  endpoint?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
}

export function SearchableSelect({
  label,
  value,
  onChange,
  options: initialOptions = [],
  endpoint,
  placeholder = 'Search & select...',
  disabled = false,
  required = false,
  id,
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState<string[]>(initialOptions);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch canonical options from backend endpoint if provided
  useEffect(() => {
    let isMounted = true;
    async function fetchOptions() {
      if (!endpoint) return;
      setIsLoading(true);
      try {
        const data = await apiClient<string[]>(endpoint, { requiresAuth: false });
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setOptions(data);
        }
      } catch (err) {
        console.warn(`Could not load options from ${endpoint}, falling back to defaults`, err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    fetchOptions();
    return () => {
      isMounted = false;
    };
  }, [endpoint]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const filteredOptions = options.filter((opt) =>
    opt.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

  const handleSelect = (opt: string) => {
    onChange(opt);
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('');
    setSearchQuery('');
  };

  return (
    <div className="relative" ref={containerRef}>
      <label className="block text-xs uppercase tracking-wider text-textSecondary font-semibold mb-1">
        {label} {required && <span className="text-accent">*</span>}
      </label>

      {/* Trigger / Display Button */}
      <div
        id={id}
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        onKeyDown={(e) => {
          if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            setIsOpen((prev) => !prev);
          }
        }}
        className={`w-full bg-surfaceHighlight border ${
          isOpen ? 'border-accent' : 'border-surfaceHighlight'
        } text-textPrimary text-sm rounded px-3 py-2.5 flex items-center justify-between cursor-pointer transition-colors ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-accent/60'
        }`}
      >
        <span className={value ? 'text-textPrimary font-medium' : 'text-textSecondary'}>
          {value || placeholder}
        </span>
        <div className="flex items-center space-x-1.5 text-textSecondary">
          {value && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-0.5 hover:text-textPrimary transition-colors"
              title="Clear selection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <ChevronDown
            className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180 text-accent' : ''}`}
          />
        </div>
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-surface border border-accent/40 rounded-lg shadow-2xl overflow-hidden backdrop-blur-md">
          {/* Search Box */}
          <div className="p-2 border-b border-surfaceHighlight bg-surfaceHighlight/50 flex items-center space-x-2">
            <Search className="w-3.5 h-3.5 text-textSecondary shrink-0" />
            <input
              type="text"
              autoFocus
              placeholder={`Search ${label.toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent text-textPrimary text-xs outline-none placeholder:text-textSecondary font-sans"
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {/* Options List */}
          <div className="max-h-52 overflow-y-auto divide-y divide-surfaceHighlight/30 text-xs">
            {isLoading ? (
              <div className="p-3 text-center text-textSecondary font-mono text-[11px]">
                Loading options...
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="p-3 text-center text-textSecondary">
                No matching {label.toLowerCase()} found
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = opt === value;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleSelect(opt)}
                    className={`w-full text-left px-3 py-2 flex items-center justify-between transition-colors ${
                      isSelected
                        ? 'bg-accent/20 text-accent font-semibold'
                        : 'text-textPrimary hover:bg-surfaceHighlight'
                    }`}
                  >
                    <span>{opt}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-accent shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
