"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import { Calendar, Wallet, TrendingUp, ArrowRight, Plus } from 'lucide-react';

interface DashboardData {
  session: {
    sim_date: string;
    portfolio_id: number;
  };
  portfolio_value: {
    cash: number;
    assets_value: number;
    total_value: number;
  };
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const fetchStatus = async () => {
    const pid = localStorage.getItem('stocksim_portfolio_id');
    if (!pid) return; // Middleware would handle redirect in real app

    try {
      const res = await api.get('/simulation/status', { params: { portfolio_id: pid } });
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTimeTravel = async (months: number) => {
    if (!data) return;
    setUpdating(true);
    
    const currentDate = new Date(data.session.sim_date);
    currentDate.setMonth(currentDate.getMonth() + months);
    const target = currentDate.toISOString().split('T')[0];

    try {
      await api.post('/simulation/forward', {
        portfolio_id: data.session.portfolio_id,
        target_date: target
      });
      await fetchStatus();
    } catch (e) {
      alert("Failed to advance time");
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading your finances...</div>;
  if (!data) return <div className="text-center py-20">Session not found. <Link href="/" className="text-primary underline">Start Over</Link></div>;

  const { session, portfolio_value } = data;

  return (
    <div className="space-y-8">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-primary text-white border-none shadow-lg shadow-primary/20">
          <div className="flex items-center gap-3 mb-2 opacity-90">
            <Calendar className="h-5 w-5" />
            <span className="text-sm font-medium">Current Date</span>
          </div>
          <p className="text-3xl font-bold tracking-tight">{session.sim_date}</p>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-2 text-gray-500">
            <Wallet className="h-5 w-5" />
            <span className="text-sm font-medium">Available Cash</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            ${portfolio_value.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-2 text-gray-500">
            <TrendingUp className="h-5 w-5" />
            <span className="text-sm font-medium">Net Worth</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            ${portfolio_value.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </Card>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left: Portfolio (Placeholder for now as per MVP) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-800">Your Holdings</h2>
            <Link href="/market">
              <Button size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-1" /> Buy Assets
              </Button>
            </Link>
          </div>
          
          <Card className="min-h-[200px] flex items-center justify-center text-gray-400 bg-gray-50/50">
             <div className="text-center">
               <p>Your portfolio is tracked here.</p>
               <Link href="/market" className="text-primary text-sm hover:underline mt-2 inline-block">
                 Browse the market to invest
               </Link>
             </div>
          </Card>
        </div>

        {/* Right: Time Control */}
        <div className="space-y-6">
           <h2 className="text-xl font-bold text-gray-800">Time Travel</h2>
           <Card className="bg-white">
             <div className="space-y-3">
               <p className="text-sm text-gray-500 mb-4">
                 Advance time to collect salary and see how your investments grow.
               </p>
               <Button 
                 className="w-full justify-between group" 
                 variant="secondary"
                 onClick={() => handleTimeTravel(1)}
                 isLoading={updating}
               >
                 <span>+ 1 Month</span>
                 <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
               </Button>
               <Button 
                 className="w-full justify-between group"
                 variant="secondary"
                 onClick={() => handleTimeTravel(6)}
                 isLoading={updating}
               >
                 <span>+ 6 Months</span>
                 <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
               </Button>
               <Button 
                 className="w-full justify-between group"
                 variant="secondary"
                 onClick={() => handleTimeTravel(12)}
                 isLoading={updating}
               >
                 <span>+ 1 Year</span>
                 <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
               </Button>
             </div>
           </Card>
        </div>

      </div>
    </div>
  );
}
