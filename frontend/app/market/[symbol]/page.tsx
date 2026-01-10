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
import FormattedMoney from '@/components/FormattedMoney';
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

interface AssetDetails {
  symbol: string;
  name: string;
  type: string;
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
  const [assetDetails, setAssetDetails] = useState<AssetDetails | null>(null);
  
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

  const [mode, setMode] = useState<'BUY' | 'SELL'>('BUY');
  const [holdingsQty, setHoldingsQty] = useState<number>(0);

  const [dataMissing, setDataMissing] = useState(false);

  useEffect(() => {
    const init = async () => {
      const date = await fetchSession();
      if (!date) return;

      try {
        // Fetch Asset Details (Full name)
        try {
            const detailsRes = await api.get(`/assets/${symbol}`);
            setAssetDetails(detailsRes.data);
        } catch (e) {
            console.warn("Could not fetch asset details", e);
        }

        const histRes = await api.get('/price/history', { params: { symbol, end_date: date } });
        const histData = histRes.data;
        setHistory(histData);

        if (histData.length > 0) {
          setCurrentPrice(histData[histData.length - 1].price);
        } else {
          // If no history, try getting current price directly (fallback)
          const priceRes = await api.get('/price', { params: { symbol, date } });
          setCurrentPrice(priceRes.data.price);
        }
        
        // Fetch holdings
        const pid = localStorage.getItem('stocksim_portfolio_id');
        if (pid) {
            const statusRes = await api.get('/simulation/status', { params: { portfolio_id: pid } });
            const userHoldings = statusRes.data.portfolio_value.holdings || [];
            const currentHolding = userHoldings.find((h: any) => h.symbol === symbol);
            setHoldingsQty(currentHolding ? currentHolding.quantity : 0);
        }

      } catch (e: any) {
        if (e.response && e.response.status === 404) {
            setDataMissing(true);
        } else {
            console.error(e);
        }
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
  
  const nativePrice = currentPrice ? convert(currentPrice) : 0;

  const handleTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBuying(true);

    const pid = localStorage.getItem('stocksim_portfolio_id');
    const quantity = Number(qty);
    const cost = quantity * nativePrice;

    if (mode === 'BUY' && cost > cash) {
      setError(`Insufficient funds.`);
      setBuying(false);
      return;
    }

    if (mode === 'SELL' && quantity > holdingsQty) {
      setError(`Insufficient holdings. You own ${holdingsQty} ${symbol}.`);
      setBuying(false);
      return;
    }

    try {
      await api.post(mode === 'BUY' ? '/portfolio/buy' : '/portfolio/sell', {
        portfolio_id: pid,
        symbol: symbol,
        quantity: quantity,
      });
      await fetchSession(); // Refresh balance
      
      // Refresh holdings
      const statusRes = await api.get('/simulation/status', { params: { portfolio_id: pid } });
      const userHoldings = statusRes.data.portfolio_value.holdings || [];
      const currentHolding = userHoldings.find((h: any) => h.symbol === symbol);
      setHoldingsQty(currentHolding ? currentHolding.quantity : 0);
      setCash(statusRes.data.portfolio_value.cash);

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
  
  if (dataMissing) return (
    <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center text-gray-400">
            <AlertCircle className="h-8 w-8" />
        </div>
        <h3 className="text-xl font-bold text-gray-900">Data Unavailable</h3>
        <p className="text-gray-500 max-w-md text-center">
            Price data for <span className="font-bold">{symbol}</span> is not available for the current simulation date ({simDate}).
            <br/>The asset might not have existed yet.
        </p>
        <Button variant="outline" onClick={() => router.back()}>
            Go Back
        </Button>
    </div>
  );

  return (
    <div className="space-y-6">
      <Button variant="outline" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to Market
      </Button>

      <div className="flex items-baseline justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          {symbol}{assetDetails?.name ? ` - ${assetDetails.name}` : ''}
          {(symbol === 'GOLD' || symbol === 'SILVER') && (
            <span className="ml-3 text-xs font-normal text-amber-600 bg-amber-50 px-2 py-1 rounded-md border border-amber-100 uppercase tracking-wider">
              Price per American Troy Ounce
            </span>
          )}
        </h1>
        <div className="text-right">
           <p className="text-sm text-gray-500">Current Price</p>
           <div className="flex justify-end">
             {currentPrice ? <FormattedMoney value={nativePrice} className="text-3xl font-bold text-gray-900" expanded /> : <span className="text-3xl font-bold text-gray-900">---</span>}
           </div>
           {simDate && (
             <p className="text-xs font-medium text-gray-400 mt-1 flex items-center justify-end gap-1">
               <span className="w-2 h-2 rounded-full bg-green-500"></span>
               {simDate}
             </p>
           )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-2 flex flex-col">
          <Card className="flex-grow flex flex-col h-full" noPadding>
             {hasMounted && history.length > 0 ? (
               <div className="flex-grow relative min-h-[40vh]">
                 <Line options={{...chartOptions, maintainAspectRatio: false}} data={chartDataConfig} />
               </div>
             ) : (
               <div className="h-full flex items-center justify-center text-gray-400 min-h-[40vh]">
                 {!hasMounted ? 'Loading chart...' : 'No price history available.'}
               </div>
             )}
          </Card>
        </div>

        <div className="flex flex-col">
          <Card className="flex flex-col" noPadding>
             {success ? (
               <div className="text-center py-6 px-4 space-y-4 animate-in fade-in zoom-in duration-300 flex flex-col justify-center">
                 <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                   <CheckCircle2 className="h-8 w-8" />
                 </div>
                 <div className="space-y-1">
                   <h3 className="text-lg font-bold text-gray-900">Transaction Successful!</h3>
                   <p className="text-sm text-gray-500">You {mode === 'BUY' ? 'bought' : 'sold'} {qty} {symbol}</p>
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
                   Make another trade
                 </button>
               </div>
             ) : (
               <div className="space-y-4 flex flex-col pt-6 px-6 pb-0">
                 <div>
                    <div className="flex bg-gray-100 p-1 rounded-lg mb-6">
                        <button 
                            className={`flex-1 py-2 text-sm font-bold rounded-md transition-all ${mode === 'BUY' ? 'bg-white text-green-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            onClick={() => setMode('BUY')}
                        >
                            Buy
                        </button>
                        <button 
                            className={`flex-1 py-2 text-sm font-bold rounded-md transition-all ${mode === 'SELL' ? 'bg-white text-red-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            onClick={() => setMode('SELL')}
                        >
                            Sell
                        </button>
                    </div>

                    <div className={`${mode === 'BUY' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'} p-3 rounded-lg flex items-center justify-between text-sm font-medium mb-6`}>
                      <span>{mode === 'BUY' ? 'Available Cash' : 'Available Holdings'}</span>
                      {mode === 'BUY' ? (
                          <FormattedMoney value={cash} expanded />
                      ) : (
                          <span className="font-bold">{holdingsQty} {symbol}</span>
                      )}
                    </div>

                    <form onSubmit={handleTrade} className="space-y-4">
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
                          <span className="text-gray-500">{mode === 'BUY' ? 'Estimated Cost' : 'Estimated Value'}</span>
                          <span className="font-bold text-gray-900">
                            <FormattedMoney value={Number(qty) * nativePrice} expanded />
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
                        className={`w-full mt-4 ${mode === 'SELL' ? 'bg-red-600 hover:bg-red-700' : ''}`}
                        isLoading={buying}
                        disabled={!qty || Number(qty) <= 0 || buying}
                      >
                        {mode} {symbol}
                      </Button>
                    </form>
                 </div>
               </div>
             )}
          </Card>
        </div>
      </div>
    </div>
  );
}