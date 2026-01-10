"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import Modal from '@/components/Modal';
import { useCurrency } from '@/context/CurrencyContext';
import { 
  Play, 
  History, 
  TrendingUp,
  Globe2,
  LineChart,
  ArrowUpRight,
  ShieldCheck,
  Activity,
  Flame
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
  const [showWakeupModal, setShowWakeupModal] = useState(false);
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

  const cleanNum = (val: any) => {
    if (typeof val !== 'string') return Number(val) || 0;
    const cleaned = val.replace(/[^0-9.]/g, '');
    return Number(cleaned) || 0;
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
    setShowWakeupModal(true);
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
        monthly_salary: cleanNum(formData.monthlyInvestment) / (selectedCurrency.rate || 1),
        monthly_expenses: 0,
        initial_cash: cleanNum(formData.investment) / (selectedCurrency.rate || 1)
      });

      localStorage.setItem('stocksim_portfolio_id', portfolioId.toString());
      router.push('/dashboard');
    } catch (error: any) {
      console.error("Simulation Start Error:", error);
      const msg = error.response?.data?.detail || error.message || "Failed to start simulation. Check backend.";
      alert(`Error: ${msg}`);
      setLoading(false); 
      setShowWakeupModal(false);
    }
  };

  return (
    <div className="flex flex-col min-h-[80vh] relative">
      <Modal 
        isOpen={showWakeupModal} 
        onClose={() => {}} // Non-closable during wakeup
        title="Heating the servers..."
      >
        <div className="space-y-4 py-4">
          <div className="flex justify-center">
            <div className="relative">
              <Flame className="h-12 w-12 text-orange-500 animate-pulse" />
              <div className="absolute inset-0 bg-orange-400 blur-xl opacity-20 animate-pulse"></div>
            </div>
          </div>
          <div className="text-center space-y-2">
            <p className="text-gray-600 font-medium">
              We are spinning up the simulation engine.
            </p>
            <p className="text-sm text-gray-400 italic">
              Kindly wait for about 50 seconds... 
            </p>
          </div>
          <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden mt-6">
            <div className="h-full bg-orange-500 w-[40%] animate-[shimmer_2s_infinite_linear] bg-gradient-to-r from-orange-500 via-orange-400 to-orange-500 bg-[length:200%_100%] shadow-[0_0_15px_rgba(249,115,22,0.5)]"></div>
          </div>
        </div>
      </Modal>
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

        {/* Main Content Grid */}
        <div className="w-full max-w-7xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center animate-in slide-in-from-bottom-8 duration-700 delay-100 fade-in">
          
          {/* Left Visuals: Historical Timeline */}
          <div className="hidden lg:flex lg:col-span-4 flex-col gap-8 justify-center items-end text-right pr-8 opacity-80">
             <div className="relative group">
               <div className="absolute inset-y-0 right-[-2.25rem] w-0.5 bg-gradient-to-b from-transparent via-blue-200 to-transparent"></div>
               
               <div className="space-y-12">
                 <div className="relative">
                   <div className="absolute right-[-2.6rem] top-1.5 w-3 h-3 rounded-full bg-blue-400 ring-4 ring-blue-50 group-hover:scale-110 transition-transform"></div>
                   <h4 className="text-lg font-bold text-gray-900">Dot Com Bubble</h4>
                   <p className="text-sm text-gray-500 font-mono">2000 - 2002</p>
                   <p className="text-xs text-blue-600 mt-1 font-medium bg-blue-50 inline-block px-2 py-0.5 rounded">-78% NASDAQ</p>
                 </div>

                 <div className="relative">
                   <div className="absolute right-[-2.6rem] top-1.5 w-3 h-3 rounded-full bg-red-400 ring-4 ring-red-50 group-hover:scale-110 transition-transform"></div>
                   <h4 className="text-lg font-bold text-gray-900">Housing Crisis</h4>
                   <p className="text-sm text-gray-500 font-mono">2007 - 2009</p>
                   <p className="text-xs text-red-600 mt-1 font-medium bg-red-50 inline-block px-2 py-0.5 rounded">-57% S&P 500</p>
                 </div>

                 <div className="relative">
                   <div className="absolute right-[-2.6rem] top-1.5 w-3 h-3 rounded-full bg-emerald-400 ring-4 ring-emerald-50 group-hover:scale-110 transition-transform"></div>
                   <h4 className="text-lg font-bold text-gray-900">Crypto Boom</h4>
                   <p className="text-sm text-gray-500 font-mono">2020 - Present</p>
                   <p className="text-xs text-emerald-600 mt-1 font-medium bg-emerald-50 inline-block px-2 py-0.5 rounded">+1000% Bitcoin</p>
                 </div>
               </div>
             </div>
          </div>

          {/* Center: Input Form */}
          <div className="col-span-1 lg:col-span-4 w-full">
            <Card className="shadow-2xl shadow-blue-900/20 border-gray-100 bg-white/90 backdrop-blur-xl relative z-10 scale-105">
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
            
            <div className="mt-8 flex items-center justify-center gap-6 text-xs font-medium text-gray-400">
               <span className="flex items-center gap-1.5">
                 <ShieldCheck className="h-4 w-4" /> No Sign-up Required
               </span>
               <span className="flex items-center gap-1.5">
                 <Globe2 className="h-4 w-4" /> Global Data
               </span>
            </div>
          </div>

          {/* Right Visuals: Pro Analytics */}
          <div className="hidden lg:flex lg:col-span-4 flex-col gap-6 pl-8">
             <div className="p-4 rounded-2xl bg-white/60 backdrop-blur border border-white shadow-sm hover:shadow-md transition-all cursor-default -rotate-2 hover:rotate-0">
               <div className="flex items-center gap-3 mb-2">
                 <div className="p-2 bg-orange-100 text-orange-600 rounded-lg">
                   <TrendingUp className="h-5 w-5" />
                 </div>
                 <div>
                   <h5 className="font-bold text-gray-900 text-sm">Real-time Replay</h5>
                   <p className="text-[10px] text-gray-500">Tick-by-tick precision</p>
                 </div>
               </div>
               <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                 <div className="h-full bg-orange-500 w-[70%] animate-pulse"></div>
               </div>
             </div>

             <div className="p-4 rounded-2xl bg-white/60 backdrop-blur border border-white shadow-sm hover:shadow-md transition-all cursor-default rotate-3 hover:rotate-0 translate-x-4">
               <div className="flex items-center gap-3 mb-2">
                 <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                   <LineChart className="h-5 w-5" />
                 </div>
                 <div>
                   <h5 className="font-bold text-gray-900 text-sm">Advanced Metrics</h5>
                   <p className="text-[10px] text-gray-500">Sharpe, Alpha, Beta</p>
                 </div>
               </div>
               <div className="flex gap-2 mt-2">
                 <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-bold">Sortino</span>
                 <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-bold">MaxDD</span>
               </div>
             </div>

             <div className="p-4 rounded-2xl bg-white/60 backdrop-blur border border-white shadow-sm hover:shadow-md transition-all cursor-default -rotate-1 hover:rotate-0">
               <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2">
                   <ShieldCheck className="h-5 w-5 text-green-600" />
                   <span className="text-xs font-bold text-gray-600 uppercase tracking-wider">Professional Grade</span>
                 </div>
                 <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
               </div>
               <p className="text-xs text-gray-500 mt-2 leading-snug">
                 Same data used by hedge funds and quant traders.
               </p>
             </div>
          </div>

        </div>
      </div>
    </div>
  );
}
