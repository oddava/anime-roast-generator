import React from 'react';

function LoadingSpinner() {
  return (
    <div className="relative w-12 h-12">
      <div className="absolute inset-0 border-4 border-[#262626] rounded-full"></div>
      <div className="absolute inset-0 border-4 border-[#3b82f6] border-t-transparent rounded-full spinner"></div>
    </div>
  );
}

export default LoadingSpinner;