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
  compactThreshold = 1000000 // Default to 1M instead of 0
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
  const formatOptions: Intl.NumberFormatOptions = {
    style: 'currency',
    currency: selectedCurrency.code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  };

  const fullValue = new Intl.NumberFormat(selectedCurrency.code === 'INR' ? 'en-IN' : 'en-US', formatOptions).format(convertedValue);

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
      title={`${fullValue} (${value.toFixed(2)} USD)`}
    >
      <span className={shouldCompact ? "cursor-help border-b border-dotted border-gray-300/50" : ""}>
        {prefix}{displayValue}
      </span>
      
      {/* Reveal Tooltip (Only if compacted or on hover for detail) */}
      <div className={`
        absolute bottom-full mb-3 right-0 z-[9999] whitespace-nowrap
        bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-2xl
        transition-all duration-200 origin-bottom-right
        ${isHovered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-2 pointer-events-none'}
      `}>
        <div className="flex flex-col items-end gap-1">
          <span className="text-base">{fullValue}</span>
          <span className="text-xs text-gray-400 font-mono">≈ ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD</span>
        </div>
        <div className="absolute -bottom-1.5 right-6 w-3 h-3 bg-gray-900 rotate-45"></div>
      </div>
    </div>
  );
}
