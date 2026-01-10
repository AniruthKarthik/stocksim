import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  noPadding?: boolean;
}

export default function Card({ children, className = '', title, noPadding = false }: CardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-gray-50">
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className={noPadding ? "" : "p-6"}>
        {children}
      </div>
    </div>
  );
}