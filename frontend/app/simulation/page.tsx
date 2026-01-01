"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';

interface SimulationStatus {
  session: {
    sim_date: string;
    cash_balance: number;
    portfolio_id: number;
    // other fields...
  };
  portfolio_value: {
    total_value: number;
    cash: number;
    assets_value: number;
  };
}

export default function SimulationDashboard() {
  const router = useRouter();
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  // Buy Form
  const [buyForm, setBuyForm] = useState({ symbol: '', quantity: '' });

  const fetchStatus = async () => {
    const portfolioId = localStorage.getItem('stocksim_portfolio_id');
    if (!portfolioId) {
      router.push('/');
      return;
    }

    try {
      const res = await api.get('/simulation/status', {
        params: { portfolio_id: portfolioId }
      });
      setStatus(res.data);
    } catch (err) {
      console.error(err);
      router.push('/'); // If error (e.g., session not found), go home
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleAdvance = async (months: number) => {
    if (!status) return;
    setProcessing(true);
    setMessage(null);

    const currentDate = new Date(status.session.sim_date);
    currentDate.setMonth(currentDate.getMonth() + months);
    const targetDate = currentDate.toISOString().split('T')[0];

    try {
      await api.post('/simulation/forward', {
        portfolio_id: status.session.portfolio_id,
        target_date: targetDate
      });
      await fetchStatus(); // Refresh data
      setMessage({ type: 'success', text: `Advanced to ${targetDate}` });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to advance time' });
    } finally {
      setProcessing(false);
    }
  };

  const handleBuy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!status) return;
    setProcessing(true);
    setMessage(null);

    try {
      await api.post('/portfolio/buy', {
        portfolio_id: status.session.portfolio_id,
        symbol: buyForm.symbol,
        quantity: parseFloat(buyForm.quantity),
        // Date is optional, backend uses current sim date
      });
      await fetchStatus();
      setMessage({ type: 'success', text: `Successfully bought ${buyForm.quantity} of ${buyForm.symbol.toUpperCase()}` });
      setBuyForm({ symbol: '', quantity: '' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Transaction failed' });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return <div className="text-center mt-20">Loading simulation...</div>;
  }

  if (!status) return null;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-primary text-white border-none shadow-md">
          <p className="text-sm opacity-90">Current Date</p>
          <p className="text-2xl font-bold">{status.session.sim_date}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Cash Balance</p>
          <p className="text-2xl font-bold text-gray-900">
            ${status.portfolio_value.cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Portfolio Value</p>
          <p className="text-2xl font-bold text-gray-900">
            ${status.portfolio_value.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </Card>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time Controls */}
        <Card title="Time Travel" className="lg:col-span-1">
          <div className="space-y-3">
            <Button 
              className="w-full justify-between" 
              onClick={() => handleAdvance(1)}
              isLoading={processing}
            >
              Advance 1 Month
            </Button>
            <Button 
              variant="secondary" 
              className="w-full" 
              onClick={() => handleAdvance(6)}
              isLoading={processing}
            >
              Advance 6 Months
            </Button>
            <Button 
               variant="secondary"
               className="w-full"
               onClick={() => handleAdvance(12)}
               isLoading={processing}
            >
              Advance 1 Year
            </Button>
          </div>
        </Card>

        {/* Investment Panel */}
        <Card title="Make Investment" className="lg:col-span-2">
          <form onSubmit={handleBuy} className="flex flex-col md:flex-row gap-4 items-end">
            <Input 
              label="Symbol (e.g. AAPL)" 
              placeholder="AAPL" 
              value={buyForm.symbol}
              onChange={(e) => setBuyForm({...buyForm, symbol: e.target.value})}
              required
            />
            <Input 
              label="Quantity" 
              type="number" 
              placeholder="10" 
              step="any"
              value={buyForm.quantity}
              onChange={(e) => setBuyForm({...buyForm, quantity: e.target.value})}
              required
            />
            <Button type="submit" isLoading={processing} className="w-full md:w-auto min-w-[120px]">
              Buy
            </Button>
          </form>
          <p className="text-xs text-gray-500 mt-4">
            * Orders are executed at the closing price of the current simulation date.
          </p>
        </Card>
      </div>
    </div>
  );
}
