import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="bg-surface border-b border-gray-200 sticky top-0 z-50">
      <div className="container-custom h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
          <span className="text-xl font-bold text-gray-900 tracking-tight">StockSim</span>
        </Link>
        <div className="flex items-center gap-4">
           {/* Placeholder for future nav items */}
           <span className="text-sm text-gray-500">v1.0</span>
        </div>
      </div>
    </nav>
  );
}
