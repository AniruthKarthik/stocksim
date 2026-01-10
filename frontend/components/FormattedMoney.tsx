"use client";

import React, { useState } from 'react';
import { useCurrency } from '@/context/CurrencyContext';

interface FormattedMoneyProps {
  value: number;
  className?: string;
  prefix?: string;
  colored?: boolean;
}

export default function FormattedMoney({ value, className = '', prefix = '', colored = false }: FormattedMoneyProps) {
  const { selectedCurrency } = useCurrency();
  const [isHovered, setIsHovered] = useState(false);

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
  }).format(value);

  // Custom formatter for INR to ensure K, L, Cr
  let compactValue;
  if (selectedCurrency.code === 'INR') {
    if (value >= 10000000) {
      compactValue = `₹${(value / 10000000).toFixed(2)}Cr`;
    } else if (value >= 100000) {
      compactValue = `₹${(value / 100000).toFixed(2)}L`;
    } else if (value >= 1000) {
      compactValue = `₹${(value / 1000).toFixed(2)}k`;
    } else {
      compactValue = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value);
    }
  } else {
    compactValue = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: selectedCurrency.code,
      notation: 'compact',
      compactDisplay: 'short',
      maximumFractionDigits: 2,
    }).format(value);
  }

  return (
    <div 
      className={`relative inline-flex flex-col items-end group ${className} ${colorClass}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span className="cursor-help border-b border-dotted border-gray-300/50">
        {prefix}{compactValue}
      </span>
      
      {/* Reveal Tooltip */}
      <div className={`
        absolute bottom-full mb-2 right-0 z-50 whitespace-nowrap
        bg-gray-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-xl
        transition-all duration-200 origin-bottom-right
        ${isHovered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-2 pointer-events-none'}
      `}>
        {fullValue}
        <div className="absolute -bottom-1 right-4 w-2 h-2 bg-gray-900 rotate-45"></div>
      </div>
    </div>
  );
}
