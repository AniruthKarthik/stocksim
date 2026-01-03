'use client';

import { useRouter } from 'next/navigation';
import { RotateCcw } from 'lucide-react';
import { useState } from 'react';
import api from '@/lib/api';
import Modal from './Modal';
import Button from './Button';

export default function ResetButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const handleReset = async () => {
    setLoading(true);
    try {
        await api.post('/reset');
        localStorage.removeItem('stocksim_portfolio_id'); // Clear local storage too
        localStorage.removeItem('stocksim_user_id');
        router.push('/');
        router.refresh(); 
    } catch (e) {
        console.error(e);
        alert('Reset failed');
    } finally {
        setLoading(false);
        setShowModal(false);
    }
  };

  return (
    <>
      <button 
        onClick={() => setShowModal(true)} 
        disabled={loading}
        className="flex items-center gap-2 text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
      >
        <RotateCcw size={18} />
        Reset
      </button>

      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Reset Application"
        footer={
          <>
             <Button variant="secondary" onClick={() => setShowModal(false)} disabled={loading}>
                Cancel
             </Button>
             <Button onClick={handleReset} isLoading={loading} className="bg-red-600 hover:bg-red-700 text-white">
                Yes, Reset Everything
             </Button>
          </>
        }
      >
        <p>
          Are you sure you want to reset everything? This will delete all portfolios, transactions, and user progress. 
          This action cannot be undone.
        </p>
      </Modal>
    </>
  );
}
