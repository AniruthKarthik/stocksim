import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export default function Input({ label, error, icon, className = '', ...props }: InputProps) {
  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider ml-1">
          {label}
        </label>
      )}
      <div className="relative group">
        <div className={`
          absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl blur-sm transition-opacity duration-300
          ${props.disabled ? 'opacity-0' : 'opacity-0 group-focus-within:opacity-100'}
        `} />
        
        <div className="relative flex items-center bg-white rounded-xl shadow-sm border border-gray-200 transition-all duration-200 group-focus-within:border-blue-500 group-focus-within:shadow-md">
          {icon && (
            <div className="pl-4 text-gray-400 group-focus-within:text-blue-500 transition-colors">
              {icon}
            </div>
          )}
          <input
            className={`
              w-full bg-transparent border-none outline-none focus:outline-none focus:ring-0 px-4 py-3.5 
              text-base font-medium text-gray-900 placeholder:text-gray-400 
              disabled:bg-gray-50 disabled:text-gray-400 rounded-xl
              ${icon ? 'pl-3' : ''}
              ${className}
            `}
            {...props}
          />
        </div>
      </div>
      {error && (
        <p className="text-xs text-red-500 ml-1 animate-in slide-in-from-top-1 fade-in duration-200">
          {error}
        </p>
      )}
    </div>
  );
}
