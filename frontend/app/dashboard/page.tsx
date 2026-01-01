"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import { Calendar, Wallet, TrendingUp, ArrowRight, Plus, PieChart as PieChartIcon, CircleDollarSign } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from 'recharts';

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

const COLORS = ['#00C853', '#009624', '#B9F6CA', '#69F0AE', '#43A047', '#2E7D32'];

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchStatus = async () => {
    const pid = localStorage.getItem('stocksim_portfolio_id');
    if (!pid) return; 

    try {
      const res = await api.get('/simulation/status', { params: { portfolio_id: pid } });
      setData(res.data);
    } catch (e: any) {
       console.error(e);
       // Handle error fetching status silently or generic
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const [customDate, setCustomDate] = useState('');

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
      target = specificDate;
    } else if (months) {
      const [y, m, d] = data.session.sim_date.split('-').map(Number);
      const dateObj = new Date(y, m - 1 + months, d);
      target = dateObj.toISOString().split('T')[0];
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

    try {
      await api.post('/simulation/forward', {
        portfolio_id: Number(pid),
        target_date: target
      });
      await fetchStatus();
      setCustomDate(''); // Reset picker
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail) || "Failed to advance time";
      setErrorMsg(msg);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading your finances...</div>;
  if (!data) return <div className="text-center py-20">Session not found. <Link href="/" className="text-primary underline">Start Over</Link></div>;

  const { session, portfolio_value } = data;
  const holdings = portfolio_value.holdings || []; // Safety check
  const pieData = holdings.map(h => ({ name: h.symbol, value: h.value }));

  return (
    <div className="space-y-8">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-primary text-white border-none shadow-lg shadow-primary/20">
          <div className="flex items-center gap-2 mb-1 opacity-90">
            <Calendar className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Current Date</span>
          </div>
          <p className="text-2xl font-bold tracking-tight">{session.sim_date}</p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <Wallet className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Wallet Balance</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            ${portfolio_value.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-1 text-gray-500">
            <TrendingUp className="h-4 w-4" />
            <span className="text-xs font-medium uppercase">Net Worth</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            ${portfolio_value.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
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
            ${(portfolio_value.assets_value - (portfolio_value.invested_value || 0)).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </Card>
      </div>
      
      {errorMsg && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg border border-red-100 text-center">
          {errorMsg}
        </div>
      )}

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left: Portfolio Table */}
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
                             ${avgCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                           </td>
                           <td className="px-6 py-4 text-gray-600 text-right text-sm">
                             ${h.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                           </td>
                           <td className="px-6 py-4 text-gray-900 text-right font-medium">
                             ${h.invested.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                           </td>
                           <td className="px-6 py-4 font-bold text-gray-900 text-right">
                             ${h.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                           </td>
                           <td className={`px-6 py-4 font-bold text-right ${pnlColor}`}>
                             <div>{isProfit ? "+" : ""}${h.pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
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
                         ${portfolio_value.invested_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                       </td>
                       <td className="px-6 py-4 text-right font-bold text-gray-800">
                         ${portfolio_value.assets_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                       </td>
                       <td className={`px-6 py-4 text-right font-bold ${portfolio_value.assets_value >= portfolio_value.invested_value ? "text-green-600" : "text-red-600"}`}>
                         ${(portfolio_value.assets_value - (portfolio_value.invested_value || 0)).toLocaleString(undefined, { minimumFractionDigits: 2 })}
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

        {/* Right: Pie Chart & Time Control */}
        <div className="space-y-6">
           <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
             <PieChartIcon className="h-5 w-5 text-gray-500" />
             Allocation
           </h2>
           
           <Card className="h-[300px] flex items-center justify-center">
             {pieData.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                 <PieChart>
                   <Pie
                     data={pieData}
                     cx="50%"
                     cy="50%"
                     innerRadius={60}
                     outerRadius={80}
                     paddingAngle={5}
                     dataKey="value"
                     nameKey="name"
                   >
                     {pieData.map((entry, index) => (
                       <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                     ))}
                   </Pie>
                   <RechartsTooltip 
                      formatter={(val: any) => `$${Number(val).toLocaleString(undefined, {maximumFractionDigits: 0})}`} 
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                   />
                   <Legend verticalAlign="bottom" height={36}/>
                 </PieChart>
               </ResponsiveContainer>
             ) : (
               <span className="text-gray-400 text-sm">No assets to display</span>
             )}
           </Card>

           <h2 className="text-xl font-bold text-gray-800 mt-8">Time Travel</h2>
           <Card className="bg-white">
             <div className="space-y-4">
               <p className="text-sm text-gray-500">
                 Jump to a specific date or fast forward.
               </p>

               {/* Custom Date Picker */}
               <div className="flex gap-2">
                  <input 
                    type="date" 
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    min={session.sim_date}
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                  />
                  <Button 
                    size="sm" 
                    onClick={() => handleTimeTravel(undefined, customDate)}
                    disabled={!customDate}
                    isLoading={updating}
                  >
                    Go
                  </Button>
               </div>

               <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-100">
                <Button 
                    size="sm"
                    variant="secondary"
                    onClick={() => handleTimeTravel(1)}
                    isLoading={updating}
                    className="text-xs px-1"
                >
                    +1 Mo
                </Button>
                <Button 
                    size="sm"
                    variant="secondary"
                    onClick={() => handleTimeTravel(6)}
                    isLoading={updating}
                    className="text-xs px-1"
                >
                    +6 Mo
                </Button>
                <Button 
                    size="sm"
                    variant="secondary"
                    onClick={() => handleTimeTravel(12)}
                    isLoading={updating}
                    className="text-xs px-1"
                >
                    +1 Yr
                </Button>
               </div>
             </div>
           </Card>
        </div>

      </div>
    </div>
  );
}
