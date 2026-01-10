import Link from 'next/link';
import { TrendingUp, LayoutDashboard, Search } from 'lucide-react';
import ResetButton from './ResetButton';
import CurrencySelector from './CurrencySelector';

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="w-[90%] 2xl:w-[80%] max-w-screen-2xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-lg group-hover:scale-105 transition-transform">
            <TrendingUp size={20} />
          </div>
          <span className="text-xl font-bold text-gray-900 tracking-tight">StockSim</span>
        </Link>
        
        <div className="flex items-center gap-6">
          <Link 
            href="/dashboard" 
            className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-primary transition-colors"
          >
            <LayoutDashboard size={18} />
            Dashboard
          </Link>
          <Link 
            href="/market" 
            className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-primary transition-colors"
          >
            <Search size={18} />
            Market
          </Link>
          <CurrencySelector />
          <ResetButton />
        </div>
      </div>
    </nav>
  );
}