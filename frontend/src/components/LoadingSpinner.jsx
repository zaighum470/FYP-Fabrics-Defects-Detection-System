import React from 'react';

const LoadingSpinner = ({ size = 'large' }) => {
  const sizeConfig = {
    small: 'h-4 w-4',
    large: 'h-8 w-8'
  };

  const spinnerClass = sizeConfig[size] || sizeConfig.large;

  return (
    <div className={`animate-spin rounded-full ${spinnerClass} border-b-2 border-blue-600`}>
    </div>
  );
};

export default LoadingSpinner;