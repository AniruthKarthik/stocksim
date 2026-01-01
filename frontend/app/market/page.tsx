"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import Card from '@/components/Card';
import { 
  ArrowRight, 
  Coins, 
  BarChart3, 
  Gem, 
  Search, 
  TrendingUp, 
  Filter,
  CheckCircle2,
  Clock
} from 'lucide-react';

interface Asset {
  symbol: string;
  name: string;
  type: string;
}

export default function MarketPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [simDate, setSimDate] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const pid = localStorage.getItem('stocksim_portfolio_id');
      try {
        // Fetch sim date just for UI indicators, not for filtering the whole list
        if (pid) {
          const statusRes = await api.get('/simulation/status', { params: { portfolio_id: pid } });
          setSimDate(statusRes.data.session.sim_date);
        }

        // Fetch ALL assets from DB (no date filter passed to backend)
        const assetsRes = await api.get('/assets');
        setAssets(assetsRes.data);
      } catch (err) {
        console.error("Error loading market data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter logic
  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         asset.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || asset.type.toUpperCase() === selectedType;
    return matchesSearch && matchesType;
  });

  const assetTypes = ['ALL', ...Array.from(new Set(assets.map(a => a.type.toUpperCase())))];

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'CRYPTO': return <Coins className="h-4 w-4" />;
      case 'COMMODITIES': return <Gem className="h-4 w-4" />;
      case 'ETFS': return <BarChart3 className="h-4 w-4" />;
      default: return <TrendingUp className="h-4 w-4" />;
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-20 space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p className="text-gray-500 font-medium">Scanning the market...</p>
    </div>
  );

  return (
    <div className="space-y-8 pb-20">
      {/* Header & Search */}
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Market Explore</h1>
          <p className="text-gray-500 mt-2 text-lg">Browse all {assets.length} tradable instruments in the system.</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-4">
          <div className="relative flex-grow">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input 
              type="text"
              placeholder="Search by ticker or company name..."
              className="w-full pl-12 pr-4 py-4 border-none rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 shadow-sm ring-1 ring-gray-100 text-lg bg-white transition-all"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <div className="flex gap-2 overflow-x-auto pb-2 lg:pb-0 no-scrollbar">
            {assetTypes.map(type => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-6 py-2 rounded-xl font-bold whitespace-nowrap transition-all flex items-center gap-2 border-2 ${
                  selectedType === type 
                  ? 'bg-primary border-primary text-white shadow-md' 
                  : 'bg-white border-transparent text-gray-500 hover:border-gray-200'
                }`}
              >
                {type !== 'ALL' && getTypeIcon(type)}
                {type}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Assets Grid */}
      {filteredAssets.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAssets.map((asset) => (
            <Link href={`/market/${asset.symbol}`} key={asset.symbol}>
              <div className="group bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-xl hover:border-primary/20 transition-all cursor-pointer relative overflow-hidden flex flex-col h-full">
                {/* Visual Accent */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full -mr-12 -mt-12 group-hover:bg-primary/10 transition-colors"></div>
                
                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors shadow-inner">
                    {getTypeIcon(asset.type)}
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-tighter">{asset.type}</span>
                    <ArrowRight className="h-5 w-5 text-gray-300 group-hover:text-primary group-hover:translate-x-1 transition-all mt-1" />
                  </div>
                </div>

                <div className="space-y-1 relative z-10 flex-grow">
                  <h3 className="text-2xl font-black text-gray-900 group-hover:text-primary transition-colors tracking-tight">
                    {asset.symbol}
                  </h3>
                  <p className="text-gray-500 font-medium line-clamp-1 group-hover:text-gray-700">
                    {asset.name}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between relative z-10">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-gray-400">
                    <Clock className="h-3 w-3" />
                    SIM DATE: {simDate || '---'}
                  </div>
                  <button className="bg-gray-50 text-gray-900 px-4 py-1.5 rounded-lg text-xs font-black group-hover:bg-primary group-hover:text-white transition-all uppercase tracking-widest">
                    Trade
                  </button>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-32 bg-white rounded-3xl shadow-sm border border-dashed border-gray-200">
          <div className="bg-gray-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-8 w-8 text-gray-300" />
          </div>
          <h3 className="text-xl font-bold text-gray-900">No assets found</h3>
          <p className="text-gray-400 mt-1">Try adjusting your search or filters.</p>
          <button 
            onClick={() => { setSearchQuery(''); setSelectedType('ALL'); }}
            className="mt-6 text-primary font-bold hover:underline underline-offset-4"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}
