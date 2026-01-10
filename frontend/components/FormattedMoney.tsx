"use client";

import React, { useState } from 'react';
import { useCurrency } from '@/context/CurrencyContext';

interface FormattedMoneyProps {
  value: number;
  className?: string;
  prefix?: string;
  colored?: boolean;
  expanded?: boolean;
  compactThreshold?: number;
}

export default function FormattedMoney({
  value,
  className = '',
  prefix = '',
  colored = false,
  expanded = false,
  compactThreshold = 0
}: FormattedMoneyProps) {
  const { selectedCurrency, convert } = useCurrency();
  const [isHovered, setIsHovered] = useState(false);

  // Convert USD value to selected currency
  const convertedValue = convert(value);

  // Determine color based on value if 'colored' is true
  const colorClass = colored 
    ? (value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-900') 
    : '';

  // Format full value (e.g. $1,234,567.89)
  const fullValue = new Intl.NumberFormat(selectedCurrency.code === 'INR' ? 'en-IN' : 'en-US', {
    style: 'currency',
    currency: selectedCurrency.code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(convertedValue);

  // Determine if we should use compact notation
  const shouldCompact = !expanded && Math.abs(convertedValue) >= compactThreshold;

  let displayValue = fullValue;

  if (shouldCompact) {
      // Custom formatter for INR to ensure K, L, Cr
      if (selectedCurrency.code === 'INR') {
        if (convertedValue >= 10000000) {
          displayValue = `₹${(convertedValue / 10000000).toFixed(2)}Cr`;
        } else if (convertedValue >= 100000) {
          displayValue = `₹${(convertedValue / 100000).toFixed(2)}L`;
        } else if (convertedValue >= 1000) {
          displayValue = `₹${(convertedValue / 1000).toFixed(2)}k`;
        } else {
          displayValue = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(convertedValue);
        }
      } else {
        displayValue = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: selectedCurrency.code,
          notation: 'compact',
          compactDisplay: 'short',
          maximumFractionDigits: 2,
        }).format(convertedValue);
      }
  }

  return (
    <div 
      className={`relative inline-flex flex-col items-end group ${className} ${colorClass}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span className={shouldCompact ? "cursor-help border-b border-dotted border-gray-300/50" : ""}>
        {prefix}{displayValue}
      </span>
      
      {/* Reveal Tooltip (Only if compacted) */}
      {shouldCompact && (
        <div className={`
          absolute bottom-full mb-2 right-0 z-50 whitespace-nowrap
          bg-gray-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-xl
          transition-all duration-200 origin-bottom-right
          ${isHovered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-2 pointer-events-none'}
        `}>
          {fullValue}
          <div className="absolute -bottom-1 right-4 w-2 h-2 bg-gray-900 rotate-45"></div>
        </div>
      )}
    </div>
  );
}
