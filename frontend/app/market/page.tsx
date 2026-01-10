"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import useSWR from 'swr';
import api from '@/lib/api';
import { 
  ArrowRight, 
  Coins, 
  BarChart3, 
  Gem, 
  Search, 
  TrendingUp, 
  Clock
} from 'lucide-react';

interface Asset {
  symbol: string;
  name: string;
  type: string;
}

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function MarketPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [visibleCount, setVisibleCount] = useState(48);
  
  const [pid, setPid] = useState<string | null>(null);

  useEffect(() => {
    setPid(localStorage.getItem('stocksim_portfolio_id'));
  }, []);

  const { data: sessionData, isLoading: isSessionLoading } = useSWR(pid ? `/simulation/status?portfolio_id=${pid}` : null, fetcher);
  const simDate = sessionData?.session?.sim_date;

  // Optimized fetching: Don't fetch assets until we know the simulation date (if a session exists)
  // This prevents the "flash" of unfiltered stocks.
  const assetsKey = (pid && !simDate) ? null : (simDate ? `/assets?date=${simDate}` : '/assets');
  const { data: assets, error, isLoading: isAssetsLoading } = useSWR(assetsKey, fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 60000,
  });

  const isLoading = isSessionLoading || isAssetsLoading;
  const assetsList: Asset[] = assets || [];

  // Filter logic
  const filteredAssets = assetsList.filter(asset => {
    const matchesSearch = asset.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         asset.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || asset.type.toUpperCase() === selectedType;
    return matchesSearch && matchesType;
  });

  // Reset visible count when filters change
  useEffect(() => {
    setVisibleCount(48);
  }, [searchQuery, selectedType]);

  // Sort logic: CRYPTO > STOCKS > COMMODITIES > MUTUALFUNDS > ETFS
  const typeOrder: Record<string, number> = {
    'CRYPTO': 1,
    'STOCKS': 2,
    'COMMODITIES': 3,
    'MUTUALFUNDS': 4,
    'MUTUAL FUNDS': 4,
    'ETFS': 5
  };

  filteredAssets.sort((a, b) => {
    const orderA = typeOrder[a.type.toUpperCase()] || 99;
    const orderB = typeOrder[b.type.toUpperCase()] || 99;
    if (orderA !== orderB) return orderA - orderB;
    return a.symbol.localeCompare(b.symbol);
  });

  const assetsToShow = filteredAssets.slice(0, visibleCount);

  const assetTypes = ['ALL', ...Array.from(new Set(assetsList.map(a => a.type.toUpperCase())))];

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'CRYPTO': return <Coins className="h-4 w-4" />;
      case 'COMMODITIES': return <Gem className="h-4 w-4" />;
      case 'ETFS': return <BarChart3 className="h-4 w-4" />;
      default: return <TrendingUp className="h-4 w-4" />;
    }
  };

  if (isLoading && !assets) return (
    <div className="flex flex-col items-center justify-center py-20 space-y-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p className="text-gray-500 font-medium">Loading market data...</p>
    </div>
  );

  return (
    <div className="space-y-8 pb-20">
      {/* Header & Search */}
      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-4">
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Market</h1>
            {simDate && (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-bold border border-gray-200 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {simDate}
              </span>
            )}
          </div>
          <p className="text-gray-500 mt-2 text-lg">
            Browse all tradable instruments in the system.
          </p>
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
      {assetsToShow.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {assetsToShow.map((asset) => (
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
          
          {visibleCount < filteredAssets.length && (
            <div className="mt-12 text-center">
              <button 
                onClick={() => setVisibleCount(prev => prev + 48)}
                className="px-8 py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-gray-200"
              >
                Load More Assets ({filteredAssets.length - visibleCount} remaining)
              </button>
            </div>
          )}
        </>
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
