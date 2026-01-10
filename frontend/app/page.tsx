"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { useCurrency } from '@/context/CurrencyContext';
import { 
  PlayCircle, 
  ArrowRight, 
  History, 
  ShieldCheck, 
  BarChart2 
} from 'lucide-react';

export default function StartPage() {
  const router = useRouter();
  const { selectedCurrency, currencies } = useCurrency();
  const [formData, setFormData] = useState({
    startDate: '2000-10-10',
    investment: '20000',
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
          const val = parseFloat(prev.investment);
          if (isNaN(val)) return prev;

          const newVal = val * (selectedCurrency.rate / prevCurrency.rate);
          const rounded = Math.round(newVal * 100) / 100;
          return { ...prev, investment: rounded.toString() };
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
      console.log("Starting simulation setup...");
      const username = `trader_${Math.floor(Math.random() * 100000)}`;
      
      console.log("Creating user...", username);
      const userRes = await api.post('/users', { username });
      const userId = userRes.data.user_id;

      console.log("Creating portfolio for user", userId);
      const portRes = await api.post('/portfolio/create', { 
        user_id: userId, 
        name: "Main Portfolio",
        currency_code: selectedCurrency.code
      });
      const portfolioId = portRes.data.id;

      console.log("Starting simulation...", portfolioId);
      // Use raw investment amount (backend will now treat it as portfolio-currency-based)
      await api.post('/simulation/start', {
        user_id: userId,
        portfolio_id: portfolioId,
        start_date: dateToSubmit,
        monthly_salary: Number(formData.investment),
        monthly_expenses: 0, 
      });

      localStorage.setItem('stocksim_portfolio_id', portfolioId.toString());
      console.log("Navigation to dashboard...");
      router.push('/dashboard');
    } catch (error: any) {
      console.error("Simulation Start Error:", error);
      const msg = error.response?.data?.detail || error.message || "Failed to start simulation. Check backend.";
      alert(`Error: ${msg}`);
      setLoading(false); // Only stop loading on error. On success, we navigate away.
    }
  };

    return (
        <div className="min-h-[80vh] grid grid-cols-1 lg:grid-cols-2 gap-12 items-center py-8">
          {/* ... existing content ... */}
          {/* (I will just replace the opening part as per the provided diff) */}

        

        {/* Left Column: Value Proposition */}

        <div className="space-y-6 animate-fade-in-up">

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider border border-primary/20">

            <ShieldCheck className="h-3 w-3" />

            Professional Grade Simulation

          </div>

          

          <div className="space-y-4">

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 tracking-tight leading-tight">

              Master your <span className="text-primary underline decoration-primary/20 underline-offset-8">strategy</span>.

            </h1>

            <p className="text-gray-500 text-base md:text-lg max-w-lg leading-relaxed">

              Travel back to any point in the last 25 years. 

              Test your conviction, learn market cycles, and build virtual wealth without the risk.

            </p>

          </div>

  

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">

            {[

              { icon: <History className="h-5 w-5 text-blue-500" />, title: "25Y History", desc: "Full daily historical prices" },

              { icon: <BarChart2 className="h-6 w-6 text-orange-500" />, title: "Real Assets", desc: "S&P 500, Crypto & more" },

            ].map((feature, i) => (

              <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow">

                <div className="p-2 rounded-lg bg-gray-50 shrink-0">{feature.icon}</div>

                <div>

                  <h3 className="font-bold text-gray-900 text-sm">{feature.title}</h3>

                  <p className="text-[11px] text-gray-500 mt-0.5">{feature.desc}</p>

                </div>

              </div>

            ))}

          </div>

        </div>

  

        {/* Right Column: Interactive Card */}

        <div className="animate-fade-in-up animation-delay-200">

          <Card className="shadow-2xl border-none ring-1 ring-black/5 p-1 bg-white rounded-[2.5rem]">

            <div className="p-6 md:p-8 space-y-8">

              <div className="space-y-2">

                <h2 className="text-xl md:text-2xl font-bold text-gray-900">Initialize Session</h2>

                <p className="text-sm text-gray-500 font-medium">Choose your starting point and commitment.</p>

              </div>

              

              <form onSubmit={handleSubmit} className="space-y-6">

                <div className="space-y-6">

                  <div className="space-y-2">

                    <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">Travel to Start Date</label>

                    <Input 

                      type="text" 

                      value={formData.startDate}

                      onChange={handleDateChange}

                      placeholder="YYYY-MM-DD"

                      className="text-lg py-6 bg-gray-50 border-transparent focus:bg-white focus:border-primary transition-all rounded-xl font-semibold"

                      required

                    />

                  </div>

                  

                  <div className="space-y-2">

                    <label className="text-xs font-bold text-gray-500 uppercase tracking-widest ml-1">

                      Monthly Investment ({selectedCurrency.code})

                    </label>

                                        <Input 

                                          type="number" 

                                          min="0"

                                          value={formData.investment}

                                          onChange={(e) => setFormData({...formData, investment: e.target.value})}

                                          placeholder="20000"

                                          className="text-lg py-6 bg-gray-50 border-transparent focus:bg-white focus:border-primary transition-all rounded-xl font-semibold"

                                          required

                                        />

                    

                  </div>

                </div>

  

                <div className="pt-2">

                  <Button 

                    type="submit" 

                    className="w-full text-base py-7 rounded-2xl shadow-lg shadow-primary/20 hover:shadow-primary/30 active:scale-[0.98] transition-all flex items-center justify-center gap-3 font-bold" 

                    isLoading={loading}

                  >

                    <PlayCircle className="h-5 w-5" />

                    Launch Simulator

                    <ArrowRight className="h-4 w-4" />

                  </Button>

                </div>

              </form>

            </div>

          </Card>

          

          {/* Footer Trust Bar */}

          <div className="mt-8 flex justify-center gap-8 text-gray-300 animate-fade-in-up animation-delay-400 grayscale opacity-50">

            {['S&P 500', 'NASDAQ', 'CRYPTO', 'COMMODITIES'].map(item => (

              <span key={item} className="text-[10px] font-black tracking-[0.2em]">{item}</span>

            ))}

          </div>

        </div>
    </div>
  );
}
