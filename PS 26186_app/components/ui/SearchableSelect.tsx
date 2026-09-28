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
      <label className="block text-[12px] font-semibold text-ink-2 mb-1.5">
        {label} {required && <span className="text-brand-500">*</span>}
      </label>

      {/* Trigger / Display Box */}
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
        className={`w-full bg-white border h-[52px] rounded-2xl px-4 flex items-center justify-between cursor-pointer transition-all shadow-sm ${
          isOpen ? 'border-brand-500 ring-2 ring-brand-100' : 'border-sky-200'
        } ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        <span className={value ? 'text-ink font-medium text-sm' : 'text-ink-3 font-medium text-sm'}>
          {value || placeholder}
        </span>
        <div className="flex items-center space-x-1.5 text-ink-3">
          {value && !disabled && (
            <button
              type="button"
              onClick={handleClear}
              className="p-0.5 hover:text-ink transition-colors"
              title="Clear selection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <ChevronDown
            className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180 text-brand-500' : ''}`}
          />
        </div>
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-sky-200 rounded-2xl shadow-[0_16px_40px_rgba(31,110,140,0.22)] overflow-hidden">
          {/* Search Box */}
          <div className="p-3 border-b border-sky-100 bg-sky-50/50 flex items-center space-x-2">
            <Search className="w-3.5 h-3.5 text-ink-3 shrink-0" />
            <input
              type="text"
              autoFocus
              placeholder={`Search ${label.toLowerCase()}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent text-ink text-sm outline-none placeholder:text-ink-3 font-medium"
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {/* Options List */}
          <div className="max-h-48 overflow-y-auto divide-y divide-sky-100 text-sm">
            {isLoading ? (
              <div className="p-3 text-center text-ink-3 font-mono text-[11px]">
                Loading options...
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="p-3 text-center text-ink-3">
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
                    className={`w-full text-left h-12 px-4 flex items-center justify-between text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-brand-100 text-brand-600 font-semibold'
                        : 'text-ink-2 hover:bg-brand-100'
                    }`}
                  >
                    <span>{opt}</span>
                    {isSelected && <Check className="w-4 h-4 text-brand-500 shrink-0" />}
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


