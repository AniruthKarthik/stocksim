"use client";

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { ArrowLeft, TrendingUp, AlertCircle } from 'lucide-react';

interface ChartData {
  date: string;
  price: number;
}

export default function AssetDetail({ params }: { params: Promise<{ symbol: string }> }) {
  const resolvedParams = use(params);
  const symbol = resolvedParams.symbol.toUpperCase();
  const router = useRouter();

  const [simDate, setSimDate] = useState<string>('');
  const [cash, setCash] = useState<number>(0);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [history, setHistory] = useState<ChartData[]>([]);
  
  const [qty, setQty] = useState('');
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);
  const [error, setError] = useState('');

  // 1. Fetch Session Status to get Date & Cash
  const fetchSession = async () => {
    const pid = localStorage.getItem('stocksim_portfolio_id');
    if (!pid) return null;
    try {
      const res = await api.get('/simulation/status', { params: { portfolio_id: pid } });
      setSimDate(res.data.session.sim_date);
      setCash(res.data.portfolio_value.cash);
      return res.data.session.sim_date;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  // 2. Fetch Price & History based on Sim Date
  useEffect(() => {
    const init = async () => {
      const date = await fetchSession();
      if (!date) return;

      try {
        // Fetch history up to sim date
        const histRes = await api.get('/price/history', { params: { symbol, end_date: date } });
        const histData = histRes.data;
        
        setHistory(histData);

        // REQUIREMENT: Current price must match last price from history
        if (histData.length > 0) {
          setCurrentPrice(histData[histData.length - 1].price);
        } else {
          // Fallback if history is empty (e.g. before 2000)
          const priceRes = await api.get('/price', { params: { symbol, date } });
          setCurrentPrice(priceRes.data.price);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [symbol]);

  const handleBuy = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBuying(true);

    const pid = localStorage.getItem('stocksim_portfolio_id');
    const cost = Number(qty) * (currentPrice || 0);

    if (cost > cash) {
      setError(`Insufficient funds. You need $${cost.toFixed(2)}.`);
      setBuying(false);
      return;
    }

    try {
      await api.post('/portfolio/buy', {
        portfolio_id: pid,
        symbol: symbol,
        quantity: Number(qty),
        // Backend handles date
      });
      alert(`Bought ${qty} ${symbol}!`);
      router.push('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail) || "Transaction failed";
      setError(msg);
    } finally {
      setBuying(false);
    }
  };

  if (loading) return <div className="text-center py-20">Loading asset data...</div>;

  return (
    <div className="space-y-6">
      <Button variant="outline" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to Market
      </Button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Chart & Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-baseline justify-between">
            <h1 className="text-3xl font-bold text-gray-900">{symbol}</h1>
            <div className="text-right">
               <p className="text-sm text-gray-500">Current Price</p>
               <p className="text-3xl font-bold text-gray-900">
                 {currentPrice ? `$${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '---'}
               </p>
            </div>
          </div>

          <Card className="p-1 h-[400px]">
             {history.length > 0 ? (
               <ResponsiveContainer width="100%" height="100%">
                 <AreaChart data={history}>
                   <defs>
                     <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                       <stop offset="5%" stopColor="#00C853" stopOpacity={0.2}/>
                       <stop offset="95%" stopColor="#00C853" stopOpacity={0}/>
                     </linearGradient>
                   </defs>
                   <XAxis 
                     dataKey="date" 
                     tickFormatter={(str) => str.substring(0, 4)} 
                     minTickGap={50}
                     tick={{fontSize: 12, fill: '#9CA3AF'}}
                     axisLine={false}
                     tickLine={false}
                   />
                   <YAxis 
                     domain={['auto', 'auto']} 
                     tick={{fontSize: 12, fill: '#9CA3AF'}}
                     axisLine={false}
                     tickLine={false}
                     tickFormatter={(val) => `$${val}`}
                   />
                   <Tooltip 
                     contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                     formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Price']}
                     labelFormatter={(label) => new Date(label).toLocaleDateString()}
                   />
                   <Area 
                     type="monotone" 
                     dataKey="price" 
                     stroke="#00C853" 
                     strokeWidth={2}
                     fillOpacity={1} 
                     fill="url(#colorPrice)"
                     dot={false}
                   />
                 </AreaChart>
               </ResponsiveContainer>
             ) : (
               <div className="h-full flex items-center justify-center text-gray-400">
                 No price history available.
               </div>
             )}
          </Card>
        </div>

        {/* Right: Action Panel */}
        <div className="space-y-6">
          <Card title="Buy Asset">
             <div className="space-y-4">
               <div className="bg-green-50 p-3 rounded-lg flex items-center justify-between text-green-800 text-sm font-medium">
                 <span>Available Cash</span>
                 <span>${cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
               </div>

               <form onSubmit={handleBuy} className="space-y-4">
                 <Input 
                   label="Quantity"
                   type="number"
                   step="any"
                   placeholder="0.00"
                   value={qty}
                   onChange={(e) => setQty(e.target.value)}
                   disabled={buying}
                   required
                 />
                 
                 {qty && currentPrice && (
                   <div className="flex justify-between text-sm py-2 border-t border-gray-100 mt-2">
                     <span className="text-gray-500">Estimated Cost</span>
                     <span className="font-bold text-gray-900">
                       ${(Number(qty) * currentPrice).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                     </span>
                   </div>
                 )}

                 {error && (
                   <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                     <AlertCircle className="h-4 w-4 shrink-0" />
                     {error}
                   </div>
                 )}

                 <Button 
                   type="submit" 
                   className="w-full" 
                   isLoading={buying}
                   disabled={!qty || Number(qty) <= 0 || buying}
                 >
                   Buy {symbol}
                 </Button>
               </form>
             </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
