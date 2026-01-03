'use client';

import { useCurrency } from '@/context/CurrencyContext';
import { Settings } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export default function CurrencySelector() {
  const { currencies, selectedCurrency, setCurrency } = useCurrency();
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [ref]);

  return (
    <div className="relative" ref={ref}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-primary transition-colors px-2 py-1 rounded-md hover:bg-gray-50"
      >
        <span>{selectedCurrency.code}</span>
        <Settings size={14} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-50">
          <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Select Currency
          </div>
          {currencies.map(c => (
            <button
              key={c.code}
              onClick={() => {
                setCurrency(c.code);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm flex items-center justify-between hover:bg-gray-50 transition-colors
                ${selectedCurrency.code === c.code ? 'text-primary font-medium bg-blue-50' : 'text-gray-700'}
              `}
            >
              <span>{c.name}</span>
              <span className="text-gray-400 font-mono text-xs">{c.symbol}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
