"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';
import { Pie } from 'react-chartjs-2';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import { Calendar, Wallet, TrendingUp, ArrowRight, Plus, PieChart as PieChartIcon, CircleDollarSign } from 'lucide-react';
import { useCurrency } from '@/context/CurrencyContext';

ChartJS.register(ArcElement, ChartTooltip, Legend);

interface Holding {
  symbol: string;
  quantity: number;
  price: number;
  value: number;
  invested: number;
  pnl: number;
  pnl_percent: number;
}

interface DashboardData {
  session: {
    sim_date: string;
    portfolio_id: number;
  };
  portfolio_value: {
    cash: number;
    assets_value: number;
    invested_value: number;
    total_value: number;
    holdings: Holding[];
  };
}

// Shades of Green (Main Theme: #00C853)
const COLORS = [
  '#00C853', // Primary Green
  '#00E676', // Lighter Green
  '#009624', // Darker Green
  '#69F0AE', // Soft Green
  '#007E33', // Deep Green
  '#B9F6CA', // Pale Green
  '#004D40', // Dark Teal Green
  '#A5D6A7', // Muted Green
];

export default function Dashboard() {
  const { format } = useCurrency();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [customDate, setCustomDate] = useState('');
  const [hasMounted, setHasMounted] = useState(false);
  const [loadingText, setLoadingText] = useState('Loading your finances...');

  useEffect(() => {
    setHasMounted(true);
    fetchStatus();
  }, []);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (loading) {
      timer = setTimeout(() => {
        setLoadingText('Waking up the server... (this can take up to a minute)');
      }, 3000);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  const fetchStatus = async () => {
    const pid = localStorage.getItem('stocksim_portfolio_id');
    if (!pid) return; 

    try {
      const res = await api.get('/simulation/status', { params: { portfolio_id: pid } });
      setData(res.data);
    } catch (e: any) {
       console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    const isDeletion = input.length < customDate.length;
    
    let raw = input.replace(/\D/g, ''); 
    let year = raw.substring(0, 4);
    let month = raw.substring(4, 6);
    let day = raw.substring(6, 8);

    if (raw.length === 5 && !isDeletion) {
      const firstMonthDigit = parseInt(raw[4]);
      if (firstMonthDigit > 1) {
        month = '0' + raw[4];
      }
    }

    if (raw.length === 7 && !isDeletion && month.length === 2) {
      const firstDayDigit = parseInt(raw[6]);
      if (firstDayDigit > 3) {
        day = '0' + raw[6];
      }
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
    setCustomDate(formatted);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && customDate && !updating) {
      handleTimeTravel(undefined, customDate);
    }
  };

  const handleTimeTravel = async (months?: number, specificDate?: string) => {
    if (!data) return;

    const pid = localStorage.getItem('stocksim_portfolio_id');
    if (!pid) {
        setErrorMsg("Portfolio ID missing. Please restart.");
        return;
    }

    setUpdating(true);
    setErrorMsg('');
    
    let target = '';

    if (specificDate) {
      // Normalize manually typed date: handle YYYY-M-D, YYYY-MM-D, etc.
      let parts = specificDate.split('-');
      if (parts.length === 3) {
        const y = parts[0];
        const m = parts[1].padStart(2, '0');
        const d = parts[2].padStart(2, '0');
        specificDate = `${y}-${m}-${d}`;
      }

      if (!/^\d{4}-\d{2}-\d{2}$/.test(specificDate)) {
          setErrorMsg("Invalid date format. Use YYYY-MM-DD");
          setUpdating(false);
          return;
      }
      target = specificDate;
    } else if (months !== undefined) {
      const [y, m, d] = data.session.sim_date.split('-').map(Number);
      let targetMonth = m + months; 
      let targetYear = y;
      while (targetMonth > 12) {
          targetMonth -= 12;
          targetYear += 1;
      }
      const maxDays = new Date(targetYear, targetMonth, 0).getDate();
      const targetDay = Math.min(d, maxDays);
      const mm = String(targetMonth).padStart(2, '0');
      const dd = String(targetDay).padStart(2, '0');
      target = `${targetYear}-${mm}-${dd}`;
    } else {
        setUpdating(false);
        return;
    }

    // Validation: Cannot go backward
    if (new Date(target) <= new Date(data.session.sim_date)) {
        setErrorMsg("You can only travel forward in time.");
        setUpdating(false);
        return;
    }

    // Validation: Cannot go past today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (new Date(target) > today) {
        setErrorMsg("You cannot travel past the current date.");
        setUpdating(false);
        return;
    }

    try {
      await api.post('/simulation/forward', {
        portfolio_id: Number(pid),
        target_date: target
      });
      await fetchStatus();
      setCustomDate('');
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail) || "Failed to advance time";
      setErrorMsg(msg);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">{loadingText}</div>;
  if (!data) return <div className="text-center py-20">Session not found. <Link href="/" className="text-primary underline">Start Over</Link></div>;

  const { session, portfolio_value } = data;
  const holdings = portfolio_value.holdings || [];
  
  const pieChartData = {
    labels: holdings.filter(h => h.value > 0).map(h => h.symbol),
    datasets: [
      {
        data: holdings.filter(h => h.value > 0).map(h => h.value),
        backgroundColor: COLORS,
        borderColor: '#ffffff',
        borderWidth: 2,
      },
    ],
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: { size: 12 }
        }
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            // Use format() but we need to strip formatting if we want raw, 
            // but for tooltip we just want the formatted string.
            // Since format returns string, we can use it.
            // However, tooltip callbacks expect string.
            return ` ${label}: ${format(value, 0)}`;
          }
        }
      }
    },
    cutout: '60%',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <Calendar className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Current Date</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{session.sim_date}</p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <Wallet className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Wallet Balance</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {format(portfolio_value.cash)}
          </p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Net Worth</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {format(portfolio_value.total_value)}
          </p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Total Invested</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {format(portfolio_value.invested_value || 0)}
          </p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <CircleDollarSign className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Investments P&L</span>
          </div>
          <p className={`text-2xl font-bold ${
            (portfolio_value.assets_value - (portfolio_value.invested_value || 0)) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {(portfolio_value.assets_value - (portfolio_value.invested_value || 0)) >= 0 ? "+" : ""}
            {format(portfolio_value.assets_value - (portfolio_value.invested_value || 0))}
          </p>
        </Card>
      </div>
      
      {errorMsg && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-100 text-center">
          {errorMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <CircleDollarSign className="h-5 w-5 text-gray-500" />
              Your Holdings
            </h2>
            <Link href="/market">
              <Button size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-1" /> Buy Assets
              </Button>
            </Link>
          </div>
          
          <Card className="overflow-hidden">
             {holdings.length > 0 ? (
               <div className="overflow-x-auto">
                 <table className="w-full text-left border-collapse">
                   <thead>
                     <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wider">
                       <th className="px-6 py-3 font-medium">Symbol</th>
                       <th className="px-6 py-3 font-medium text-right">Inv. Price</th>
                       <th className="px-6 py-3 font-medium text-right">Curr. Price</th>
                       <th className="px-6 py-3 font-medium text-right">Invested</th>
                       <th className="px-6 py-3 font-medium text-right">Curr. Value</th>
                       <th className="px-6 py-3 font-medium text-right">P&L</th>
                     </tr>
                   </thead>
                   <tbody className="divide-y divide-gray-100">
                     {holdings.map((h) => {
                       const isProfit = h.pnl >= 0;
                       const pnlColor = isProfit ? "text-green-600" : "text-red-600";
                       const avgCost = h.quantity > 0 ? h.invested / h.quantity : 0;
                       return (
                         <tr key={h.symbol} className="hover:bg-gray-50 transition-colors">
                           <td className="px-6 py-4">
                             <div className="font-semibold text-gray-900">{h.symbol}</div>
                             <div className="text-xs text-gray-400">{h.quantity.toFixed(4)} qty</div>
                           </td>
                           <td className="px-6 py-4 text-gray-600 text-right text-sm">
                             {format(avgCost)}
                           </td>
                           <td className="px-6 py-4 text-gray-600 text-right text-sm">
                             {format(h.price)}
                           </td>
                           <td className="px-6 py-4 text-gray-900 text-right font-medium">
                             {format(h.invested)}
                           </td>
                           <td className="px-6 py-4 font-bold text-gray-900 text-right">
                             {format(h.value)}
                           </td>
                           <td className={`px-6 py-4 font-bold text-right ${pnlColor}`}>
                             <div>{isProfit ? "+" : ""}{format(h.pnl)}</div>
                             <div className="text-xs opacity-80">({isProfit ? "+" : ""}{h.pnl_percent.toFixed(2)}%)</div>
                           </td>
                         </tr>
                       );
                     })}
                   </tbody>
                   <tfoot className="bg-gray-50 border-t border-gray-200">
                     <tr>
                       <td colSpan={3} className="px-6 py-4 text-right font-medium text-gray-600">Total Portfolio</td>
                       <td className="px-6 py-4 text-right font-bold text-gray-800">
                         {format(portfolio_value.invested_value || 0)}
                       </td>
                       <td className="px-6 py-4 text-right font-bold text-gray-800">
                         {format(portfolio_value.assets_value)}
                       </td>
                       <td className={`px-6 py-4 text-right font-bold ${portfolio_value.assets_value >= (portfolio_value.invested_value || 0) ? "text-green-600" : "text-red-600"}`}>
                         {format(portfolio_value.assets_value - (portfolio_value.invested_value || 0))}
                       </td>
                     </tr>
                   </tfoot>
                 </table>
               </div>
             ) : (
               <div className="text-center py-10 text-gray-400">
                 <p className="mb-2">Your portfolio is empty.</p>
                 <Link href="/market" className="text-primary text-sm hover:underline">
                   Browse the market to start investing
                 </Link>
               </div>
             )}
          </Card>
        </div>

        <div className="space-y-6">
           <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
             <PieChartIcon className="h-5 w-5 text-gray-500" />
             Allocation
           </h2>
           
           <Card className="h-[450px] flex items-center justify-center p-4">
             {hasMounted && pieChartData.labels.length > 0 ? (
               <Pie options={pieOptions} data={pieChartData} />
             ) : (
               <span className="text-gray-400 text-sm">{!hasMounted ? 'Loading chart...' : 'No assets to display'}</span>
             )}
           </Card>

           <h2 className="text-xl font-bold text-gray-800 mt-8">Time Travel</h2>
           <Card className="bg-white">
             <div className="space-y-4">
               <p className="text-sm text-gray-500">
                 Jump to a specific date or fast forward.
               </p>
               <div className="flex gap-2">
                  <input 
                    type="text" 
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    placeholder="YYYY-MM-DD"
                    value={customDate}
                    onChange={handleDateChange}
                    onKeyDown={handleKeyDown}
                  />
                  <Button size="sm" onClick={() => handleTimeTravel(undefined, customDate)} disabled={!customDate} isLoading={updating}>Go</Button>
               </div>
               <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-100">
                <Button size="sm" variant="secondary" onClick={() => handleTimeTravel(1)} isLoading={updating} className="text-xs px-1">+1 Mo</Button>
                <Button size="sm" variant="secondary" onClick={() => handleTimeTravel(6)} isLoading={updating} className="text-xs px-1">+6 Mo</Button>
                <Button size="sm" variant="secondary" onClick={() => handleTimeTravel(12)} isLoading={updating} className="text-xs px-1">+1 Yr</Button>
               </div>
             </div>
           </Card>
        </div>
      </div>
    </div>
  );
}