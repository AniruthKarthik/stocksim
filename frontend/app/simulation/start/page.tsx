"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Input from '@/components/Input';

export default function StartSimulation() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: '',
    startDate: '2020-01-01',
    salary: '5000',
    expenses: '3000',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 1. Create User
      // Note: In a real app, we'd check if user exists or login. 
      // Here, we try to create one. If it fails (exists), we might handle that (MVP: Assume unique or just fail).
      // Actually, let's try to just create. If 400, maybe try to fetch? 
      // The backend says "User already exists or error". 
      // For MVP simplicity, let's assume unique username or user handles the error.
      
      const userRes = await api.post('/users', { username: formData.username });
      const userId = userRes.data.user_id;

      // 2. Create Portfolio
      const portRes = await api.post('/portfolio/create', { 
        user_id: userId, 
        name: `${formData.username}'s Portfolio` 
      });
      const portfolioId = portRes.data.id;

      // 3. Start Simulation
      await api.post('/simulation/start', {
        user_id: userId,
        portfolio_id: portfolioId,
        start_date: formData.startDate,
        monthly_salary: parseFloat(formData.salary),
        monthly_expenses: parseFloat(formData.expenses),
      });

      // 4. Save session
      localStorage.setItem('stocksim_user_id', userId.toString());
      localStorage.setItem('stocksim_portfolio_id', portfolioId.toString());

      // 5. Redirect
      router.push('/simulation');

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-[60vh]">
      <Card title="Start New Simulation" className="w-full max-w-md">
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="Username"
            name="username"
            placeholder="Enter a unique username"
            value={formData.username}
            onChange={handleChange}
            required
          />
          
          <Input
            label="Start Date (YYYY-MM-DD)"
            name="startDate"
            type="date"
            value={formData.startDate}
            onChange={handleChange}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Monthly Salary ($)"
              name="salary"
              type="number"
              min="0"
              value={formData.salary}
              onChange={handleChange}
              required
            />
            <Input
              label="Monthly Expenses ($)"
              name="expenses"
              type="number"
              min="0"
              value={formData.expenses}
              onChange={handleChange}
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}

          <Button 
            type="submit" 
            isLoading={loading} 
            className="w-full"
          >
            Launch Simulator
          </Button>
        </form>
      </Card>
    </div>
  );
}
