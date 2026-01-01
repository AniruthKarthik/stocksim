"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import Card from '@/components/Card';
import { ArrowRight, Coins, BarChart3, Gem } from 'lucide-react';

interface Asset {
  symbol: string;
  name: string;
  type: string;
}

export default function MarketPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const pid = localStorage.getItem('stocksim_portfolio_id');
      let simDate = null;

      try {
        if (pid) {
          const statusRes = await api.get('/simulation/status', { params: { portfolio_id: pid } });
          simDate = statusRes.data.session.sim_date;
        }

        const assetsRes = await api.get('/assets', { 
          params: { date: simDate } 
        });
        setAssets(assetsRes.data);
      } catch (err) {
        console.error("Error loading market data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Group assets by type
  const grouped = assets.reduce((acc, asset) => {
    const type = asset.type.toUpperCase();
    if (!acc[type]) acc[type] = [];
    acc[type].push(asset);
    return acc;
  }, {} as Record<string, Asset[]>);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'CRYPTO': return <Coins className="h-5 w-5 text-purple-500" />;
      case 'COMMODITIES': return <Gem className="h-5 w-5 text-yellow-500" />;
      default: return <BarChart3 className="h-5 w-5 text-blue-500" />;
    }
  };

  if (loading) return <div className="text-center py-20">Loading market data...</div>;

  return (
    <div className="space-y-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Market</h1>
        <p className="text-gray-500">Discover and trade assets from the past.</p>
      </div>

      {Object.entries(grouped).map(([type, list]) => (
        <div key={type} className="space-y-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            {getTypeIcon(type)}
            {type}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((asset) => (
              <Link href={`/market/${asset.symbol}`} key={asset.symbol}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer group border-l-4 border-l-transparent hover:border-l-primary h-full">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-bold text-gray-900">{asset.symbol}</h3>
                      <p className="text-sm text-gray-500">{asset.name}</p>
                    </div>
                    <div className="bg-gray-50 p-2 rounded-full group-hover:bg-green-50 transition-colors">
                      <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-primary" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
