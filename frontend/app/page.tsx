"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { PlayCircle } from 'lucide-react';

export default function StartPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    startDate: '2016-01-01',
    salary: '5000',
    expenses: '3000',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. Create User (Anonymous for now, random suffix)
      const username = `trader_${Math.floor(Math.random() * 10000)}`;
      const userRes = await api.post('/users', { username });
      const userId = userRes.data.user_id;

      // 2. Create Portfolio
      const portRes = await api.post('/portfolio/create', { 
        user_id: userId, 
        name: "Main Portfolio" 
      });
      const portfolioId = portRes.data.id;

      // 3. Start Session
      await api.post('/simulation/start', {
        user_id: userId,
        portfolio_id: portfolioId,
        start_date: formData.startDate,
        monthly_salary: Number(formData.salary),
        monthly_expenses: Number(formData.expenses),
      });

      // 4. Save & Redirect
      localStorage.setItem('stocksim_portfolio_id', portfolioId.toString());
      router.push('/dashboard');

    } catch (error) {
      console.error(error);
      alert("Failed to start simulation. Check backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center">
      <div className="mb-8 text-center space-y-2">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
          Stock<span className="text-primary">Sim</span>
        </h1>
        <p className="text-gray-500 text-lg">Travel back in time. Master the market.</p>
      </div>

      <Card className="w-full max-w-md shadow-lg border-none ring-1 ring-gray-100">
        <div className="p-2">
          <h2 className="text-xl font-bold text-gray-800 mb-6 text-center">Setup Simulation</h2>
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input 
              label="Start Date" 
              type="date" 
              value={formData.startDate}
              max={new Date().toISOString().split('T')[0]}
              onChange={(e) => setFormData({...formData, startDate: e.target.value})}
              required
            />
            
            <div className="grid grid-cols-2 gap-4">
              <Input 
                label="Monthly Income" 
                type="number" 
                min="0"
                value={formData.salary}
                onChange={(e) => setFormData({...formData, salary: e.target.value})}
              />
              <Input 
                label="Expenses" 
                type="number" 
                min="0"
                value={formData.expenses}
                onChange={(e) => setFormData({...formData, expenses: e.target.value})}
              />
            </div>

            <Button 
              type="submit" 
              className="w-full text-base py-3 mt-2" 
              isLoading={loading}
            >
              <PlayCircle className="mr-2 h-5 w-5" />
              Enter Simulation
            </Button>
          </form>
        </div>
      </Card>
      
      <p className="mt-8 text-sm text-gray-400">
        Simulates real historical data. No real money involved.
      </p>
    </div>
  );
}
