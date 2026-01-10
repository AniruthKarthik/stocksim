"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { useCurrency } from '@/context/CurrencyContext';
import { 
  Play, 
  History, 
  TrendingUp,
  Globe2,
  LineChart,
  ArrowUpRight,
  ShieldCheck,
  Activity
} from 'lucide-react';

export default function StartPage() {
  const router = useRouter();
  const { selectedCurrency, currencies } = useCurrency();
  const [formData, setFormData] = useState({
    startDate: '2000-10-10',
    investment: '20000',
    monthlyInvestment: '0',
  });
  const [loading, setLoading] = useState(false);
  const prevCurrencyRef = useRef(selectedCurrency.code);

  // Auto-convert investment amount when currency changes
  useEffect(() => {
    if (prevCurrencyRef.current !== selectedCurrency.code && currencies.length > 0) {
      const prevCode = prevCurrencyRef.current;
      const prevCurrency = currencies.find(c => c.code === prevCode);

      if (prevCurrency && prevCurrency.rate && selectedCurrency.rate) {
        setFormData(prev => {
          const convert = (valStr: string) => {
            const val = parseFloat(valStr);
            if (isNaN(val)) return valStr;
            const newVal = val * (selectedCurrency.rate / prevCurrency.rate);
            return (Math.round(newVal * 100) / 100).toString();
          };

          return { 
            ...prev, 
            investment: convert(prev.investment),
            monthlyInvestment: convert(prev.monthlyInvestment)
          };
        });
      }
    }
    prevCurrencyRef.current = selectedCurrency.code;
  }, [selectedCurrency, currencies]);

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    const isDeletion = input.length < formData.startDate.length;
    
    let raw = input.replace(/\D/g, ''); 
    if (raw.length > 8) raw = raw.substring(0, 8);
    
    let year = raw.substring(0, 4);
    let month = raw.substring(4, 6);
    let day = raw.substring(6, 8);

    if (raw.length === 5 && !isDeletion) {
      const firstMonthDigit = parseInt(raw[4]);
      if (firstMonthDigit > 1) month = '0' + raw[4];
    }

    if (raw.length === 7 && !isDeletion && month.length === 2) {
      const firstDayDigit = parseInt(raw[6]);
      if (firstDayDigit > 3) day = '0' + raw[6];
    }

    let formatted = year;
    if (year.length === 4) {
      if (!isDeletion || month.length > 0) formatted += '-';
      if (month.length > 0) {
        formatted += month;
        if (month.length === 2) {
          if (!isDeletion || day.length > 0) formatted += '-';
          if (day.length > 0) formatted += day;
        }
      }
    }
    setFormData({ ...formData, startDate: formatted });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Normalize date
    let dateToSubmit = formData.startDate;
    let dateParts = formData.startDate.split('-');
    if (dateParts.length === 3) {
      const y = dateParts[0];
      const m = dateParts[1].padStart(2, '0');
      const d = dateParts[2].padStart(2, '0');
      dateToSubmit = `${y}-${m}-${d}`;
    }
    
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dateToSubmit)) {
      alert("Please enter a valid date (YYYY-MM-DD)");
      return;
    }

    const selectedDate = new Date(dateToSubmit);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (selectedDate > today) {
      alert("You cannot travel to the future. Please select a date in the past or today.");
      return;
    }

    setLoading(true);
    try {
      const username = `trader_${Math.floor(Math.random() * 100000)}`;
      
      const userRes = await api.post('/users', { username });
      const userId = userRes.data.user_id;

      const portRes = await api.post('/portfolio/create', { 
        user_id: userId, 
        name: "Main Portfolio",
        currency_code: selectedCurrency.code
      });
      const portfolioId = portRes.data.id;

      await api.post('/simulation/start', {
        user_id: userId,
        portfolio_id: portfolioId,
        start_date: dateToSubmit,
        monthly_salary: Number(formData.monthlyInvestment),
        monthly_expenses: 0,
        initial_cash: Number(formData.investment)
      });

      localStorage.setItem('stocksim_portfolio_id', portfolioId.toString());
      router.push('/dashboard');
    } catch (error: any) {
      console.error("Simulation Start Error:", error);
      const msg = error.response?.data?.detail || error.message || "Failed to start simulation. Check backend.";
      alert(`Error: ${msg}`);
      setLoading(false); 
    }
  };

  return (
    <div className="flex flex-col min-h-[85vh] relative">
      {/* Background Decor */}
      <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[60vw] h-[40vh] bg-gradient-to-b from-blue-50/80 to-transparent rounded-full blur-3xl opacity-60" />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center py-12">
        {/* Header Section */}
        <div className="text-center space-y-6 max-w-3xl mx-auto mb-12 px-4 animate-in slide-in-from-bottom-8 duration-700 fade-in">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-gray-200 shadow-sm text-xs font-semibold text-gray-600 mb-4">
            <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
            Live Market Data Available
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-gray-900 leading-[1.1]">
            Predict the market <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-br from-gray-900 to-gray-500">without the risk.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-500 max-w-xl mx-auto leading-relaxed">
            Travel back in time and trade on historical data. 
            Test your strategies against the Dot Com Bubble, 2008 Crash, or the Crypto Boom.
          </p>
        </div>

        {/* Main Interaction Card */}
        <div className="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch px-4">
          
          {/* Left: Input Form */}
          <div className="lg:col-span-5 w-full animate-in slide-in-from-bottom-8 duration-700 delay-100 fade-in flex flex-col">
            <Card className="shadow-xl shadow-gray-200/50 border-gray-100 bg-white/80 backdrop-blur-lg h-full">
              <div className="p-6 md:p-8 space-y-8">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-600" />
                    Configure Simulation
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">Set your starting conditions</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                   <div className="space-y-5">
                    <Input 
                      label="Start Date"
                      type="text" 
                      value={formData.startDate}
                      onChange={handleDateChange}
                      placeholder="YYYY-MM-DD"
                      icon={<History className="h-4 w-4" />}
                      required
                    />
                    
                    <Input 
                      label={`Initial Capital (${selectedCurrency.code})`}
                      type="number" 
                      min="0"
                      value={formData.investment}
                      onChange={(e) => setFormData({...formData, investment: e.target.value})}
                      placeholder="20000"
                      icon={<span className="text-xs font-bold">{selectedCurrency.symbol}</span>}
                      required
                    />

                    <Input 
                      label={`Monthly Contribution (${selectedCurrency.code})`}
                      type="number" 
                      min="0"
                      value={formData.monthlyInvestment}
                      onChange={(e) => setFormData({...formData, monthlyInvestment: e.target.value})}
                      placeholder="5000"
                      icon={<span className="text-xs font-bold">{selectedCurrency.symbol}</span>}
                    />
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full py-6 text-base font-semibold shadow-lg shadow-blue-600/20 bg-gray-900 hover:bg-gray-800 text-white rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98]" 
                    isLoading={loading}
                  >
                    <div className="flex items-center justify-center gap-2">
                      <Play className="h-4 w-4 fill-current" />
                      Start Simulation
                    </div>
                  </Button>
                </form>
              </div>
            </Card>
            
            <div className="mt-6 flex items-center justify-center gap-6 text-xs font-medium text-gray-400">
               <span className="flex items-center gap-1.5">
                 <ShieldCheck className="h-4 w-4" /> No Sign-up Required
               </span>
               <span className="flex items-center gap-1.5">
                 <Globe2 className="h-4 w-4" /> Global Data
               </span>
            </div>
          </div>

          {/* Right: Feature Highlights (Visual) */}
          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4 animate-in slide-in-from-bottom-8 duration-700 delay-200 fade-in">
             <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
               <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 mb-4">
                 <History className="h-5 w-5" />
               </div>
               <h4 className="font-bold text-gray-900">25+ Years History</h4>
               <p className="text-sm text-gray-500 mt-2 leading-relaxed">
                 Access granular daily data for stocks, crypto, and commodities dating back to 2000.
               </p>
             </div>

             <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
               <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center text-purple-600 mb-4">
                 <LineChart className="h-5 w-5" />
               </div>
               <h4 className="font-bold text-gray-900">Real-time Analytics</h4>
               <p className="text-sm text-gray-500 mt-2 leading-relaxed">
                 Track your P&L, Sharpe ratio, and portfolio beta as if you were trading live.
               </p>
             </div>

             <div className="p-6 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow sm:col-span-2">
               <div className="flex items-start justify-between">
                 <div>
                   <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 mb-4">
                     <TrendingUp className="h-5 w-5" />
                   </div>
                   <h4 className="font-bold text-gray-900">Multi-Asset Support</h4>
                   <p className="text-sm text-gray-500 mt-2 leading-relaxed max-w-md">
                     Don't limit yourself to stocks. Trade Bitcoin, Gold, ETFs, and Mutual Funds all in one unified portfolio simulation.
                   </p>
                 </div>
                 <div className="hidden sm:flex -space-x-2">
                    {['AAPL', 'BTC', 'GLD', 'VTI'].map((ticker, i) => (
                      <div key={ticker} className="h-8 px-3 rounded-full bg-gray-50 border border-white shadow-sm flex items-center text-[0.65rem] font-bold text-gray-600 z-10" style={{ marginLeft: i > 0 ? '-0.5rem' : 0 }}>
                        {ticker}
                      </div>
                    ))}
                 </div>
               </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
