'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import api from '@/lib/api';

export interface Currency {
  code: string;
  name: string;
  symbol: string;
  rate: number;
}

interface CurrencyContextType {
  currencies: Currency[];
  selectedCurrency: Currency;
  setCurrency: (code: string) => void;
  format: (amount: number, fractionDigits?: number) => string;
  convert: (amount: number) => number;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState<Currency>({
    code: 'USD',
    name: 'United States Dollar',
    symbol: '$',
    rate: 1.0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrencies();
  }, []);

  const fetchCurrencies = async () => {
    try {
      const res = await api.get<Currency[]>('/currencies');
      setCurrencies(res.data);
      
      // Restore selection
      const saved = localStorage.getItem('stocksim_currency');
      if (saved) {
        const found = res.data.find(c => c.code === saved);
        if (found) setSelectedCurrency(found);
      }
    } catch (e) {
      console.error("Failed to fetch currencies", e);
    } finally {
      setLoading(false);
    }
  };

  const setCurrency = (code: string) => {
    const found = currencies.find(c => c.code === code);
    if (found) {
      setSelectedCurrency(found);
      localStorage.setItem('stocksim_currency', code);
    }
  };

  const convert = (amount: number) => {
    return amount * selectedCurrency.rate;
  };

  const format = (amount: number, fractionDigits: number = 2) => {
    const val = convert(amount);
    const locale = selectedCurrency.code === 'INR' ? 'en-IN' : 'en-US';
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: selectedCurrency.code,
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(val);
  };

  return (
    <CurrencyContext.Provider value={{ currencies, selectedCurrency, setCurrency, format, convert }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
}
