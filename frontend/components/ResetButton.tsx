'use client';

import { useRouter } from 'next/navigation';
import { RotateCcw } from 'lucide-react';
import { useState } from 'react';
import api from '@/lib/api';

export default function ResetButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    if (!confirm("Are you sure you want to reset everything? This cannot be undone.")) return;
    
    setLoading(true);
    try {
        await api.post('/reset');
        router.push('/');
        router.refresh(); 
    } catch (e) {
        console.error(e);
        alert('Reset failed');
    } finally {
        setLoading(false);
    }
  };

  return (
    <button 
      onClick={handleReset} 
      disabled={loading}
      className="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
    >
      <RotateCcw size={18} />
      {loading ? 'Resetting...' : 'Reset'}
    </button>
  );
}
