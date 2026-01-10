"use client";

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { ArrowLeft, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useCurrency } from '@/context/CurrencyContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

interface ChartData {
  date: string;
  price: number;
}

export default function AssetDetail({ params }: { params: Promise<{ symbol: string }> }) {
  const { format, convert, selectedCurrency } = useCurrency();
  const resolvedParams = use(params);
  const symbol = resolvedParams.symbol.toUpperCase();
  const router = useRouter();

  const [simDate, setSimDate] = useState<string>('');
  const [cash, setCash] = useState<number>(0);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [history, setHistory] = useState<ChartData[]>([]);
  
  const [qty, setQty] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingText, setLoadingText] = useState('Loading asset data...');
  const [buying, setBuying] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [hasMounted, setHasMounted] = useState(false);

  useEffect(() => {
    setHasMounted(true);
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

  useEffect(() => {
    const init = async () => {
      const date = await fetchSession();
      if (!date) return;

      try {
        const histRes = await api.get('/price/history', { params: { symbol, end_date: date } });
        const histData = histRes.data;
        
        console.log("FINAL CHART DATA:", histData);
        setHistory(histData);

        if (histData.length > 0) {
          setCurrentPrice(histData[histData.length - 1].price);
        } else {
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

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: (context: any) => format(context.parsed.y)
        }
      },
    },
    scales: {
      x: {
        display: true,
        grid: { display: false },
        ticks: {
          maxTicksLimit: 8,
          autoSkip: true,
          callback: function(val: any, index: number) {
            const label = (this as any).getLabelForValue(val);
            return typeof label === 'string' ? label.split('-')[0] : label;
          }
        }
      },
      y: {
        display: true,
        grid: { color: '#f3f4f6' },
        ticks: {
          callback: (val: any) => selectedCurrency.symbol + val.toLocaleString()
        }
      },
    },
    elements: {
      point: { radius: 0 },
      line: { tension: 0.1 }
    },
    interaction: {
      intersect: false,
      axis: 'x' as const,
    },
  };

  const chartDataConfig = {
    labels: history.map(d => d.date),
    datasets: [
      {
        fill: true,
        label: 'Price',
        data: history.map(d => convert(d.price)),
        borderColor: '#00C853',
        backgroundColor: 'rgba(0, 200, 83, 0.1)',
        borderWidth: 2,
      },
    ],
  };

  const handleBuy = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBuying(true);

    const pid = localStorage.getItem('stocksim_portfolio_id');
    const cost = Number(qty) * (currentPrice || 0);

    if (cost > cash) {
      setError(`Insufficient funds. You need ${format(cost)}.`);
      setBuying(false);
      return;
    }

    try {
      await api.post('/portfolio/buy', {
        portfolio_id: pid,
        symbol: symbol,
        quantity: Number(qty),
      });
      // Fetch fresh session data to get the normalized cash value in USD
      // This prevents issues where backend returns raw local currency while frontend expects USD
      await fetchSession();
      setSuccess(true);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail) || "Transaction failed";
      setError(msg);
    } finally {
      setBuying(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">{loadingText}</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Button variant="outline" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to Market
      </Button>

      <div className="flex items-baseline justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          {symbol}
          {(symbol === 'GOLD' || symbol === 'SILVER') && (
            <span className="ml-3 text-xs font-normal text-amber-600 bg-amber-50 px-2 py-1 rounded-md border border-amber-100 uppercase tracking-wider">
              Price per American Troy Ounce
            </span>
          )}
        </h1>
        <div className="text-right">
           <p className="text-sm text-gray-500">Current Price</p>
           <p className="text-3xl font-bold text-gray-900">
             {currentPrice ? format(currentPrice) : '---'}
           </p>
           {simDate && (
             <p className="text-xs font-medium text-gray-400 mt-1 flex items-center justify-end gap-1">
               <span className="w-2 h-2 rounded-full bg-green-500"></span>
               {simDate}
             </p>
           )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
        <div className="lg:col-span-2 flex flex-col">
          <Card className="p-4 flex-grow flex flex-col h-full">
             {hasMounted && history.length > 0 ? (
               <div className="flex-grow relative min-h-[300px]">
                 <Line options={{...chartOptions, maintainAspectRatio: false}} data={chartDataConfig} />
               </div>
             ) : (
               <div className="h-full flex items-center justify-center text-gray-400 min-h-[300px]">
                 {!hasMounted ? 'Loading chart...' : 'No price history available.'}
               </div>
             )}
          </Card>
        </div>

        <div className="flex flex-col">
          <Card title="Buy Asset" className="flex-grow flex flex-col">
             {success ? (
               <div className="text-center py-6 space-y-4 animate-in fade-in zoom-in duration-300">
                 <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                   <CheckCircle2 className="h-8 w-8" />
                 </div>
                 <div className="space-y-1">
                   <h3 className="text-lg font-bold text-gray-900">Purchase Successful!</h3>
                   <p className="text-sm text-gray-500">You bought {qty} {symbol}</p>
                 </div>
                 <Button 
                   className="w-full mt-4" 
                   onClick={() => window.location.href = '/dashboard'}
                 >
                   View Portfolio
                 </Button>
                 <button 
                   onClick={() => { setSuccess(false); setQty(''); }}
                   className="text-xs text-gray-400 hover:text-gray-600 underline"
                 >
                   Buy more {symbol}
                 </button>
               </div>
             ) : (
               <div className="space-y-4">
                 <div className="bg-green-50 p-3 rounded-lg flex items-center justify-between text-green-800 text-sm font-medium">
                   <span>Available Cash</span>
                   <span>{format(cash)}</span>
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
                         {format(Number(qty) * currentPrice)}
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
             )}
          </Card>
        </div>
      </div>
    </div>
  );
}