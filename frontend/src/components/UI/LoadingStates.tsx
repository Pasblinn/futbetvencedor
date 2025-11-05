import React from 'react';
import { RefreshCw, Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <Loader2 className={`animate-spin text-primary-400 ${sizeClasses[size]} ${className}`} />
  );
};

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rectangular'
}) => {
  const baseClasses = 'animate-pulse bg-bg-secondary';
  const variantClasses = {
    text: 'h-4 rounded',
    rectangular: 'rounded-lg',
    circular: 'rounded-full'
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`} />
  );
};

interface CardSkeletonProps {
  showActions?: boolean;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ showActions = false }) => {
  return (
    <div className="bg-bg-card rounded-lg border border-border-subtle p-6 animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <Skeleton variant="circular" className="w-10 h-10" />
        <div className="flex-1">
          <Skeleton variant="text" className="w-32 mb-2" />
          <Skeleton variant="text" className="w-48" />
        </div>
      </div>

      <div className="space-y-3">
        <Skeleton variant="rectangular" className="h-20" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton variant="text" className="h-8" />
          <Skeleton variant="text" className="h-8" />
          <Skeleton variant="text" className="h-8" />
        </div>
      </div>

      {showActions && (
        <div className="flex gap-2 mt-4">
          <Skeleton variant="rectangular" className="w-20 h-8" />
          <Skeleton variant="rectangular" className="w-24 h-8" />
        </div>
      )}
    </div>
  );
};

interface LoadingStateProps {
  type?: 'spinner' | 'skeleton' | 'card';
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  type = 'spinner',
  message = 'Carregando...',
  className = ''
}) => {
  if (type === 'skeleton') {
    return (
      <div className={`space-y-4 ${className}`}>
        {Array.from({ length: 3 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return <CardSkeleton />;
  }

  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <LoadingSpinner size="lg" />
      <p className="text-text-secondary mt-3">{message}</p>
    </div>
  );
};

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    loading?: boolean;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action
}) => {
  return (
    <div className="text-center py-12">
      {icon && (
        <div className="w-16 h-16 bg-bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
          {icon}
        </div>
      )}

      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>

      {description && (
        <p className="text-text-secondary mb-6">{description}</p>
      )}

      {action && (
        <button
          onClick={action.onClick}
          disabled={action.loading}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-all flex items-center gap-2 mx-auto"
        >
          {action.loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          {action.label}
        </button>
      )}
    </div>
  );
};

// Dashboard Skeleton
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg border border-slate-200 animate-pulse">
            <Skeleton variant="text" className="w-24 mb-2" />
            <Skeleton variant="text" className="w-16 h-8 mb-2" />
            <Skeleton variant="text" className="w-32" />
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} showActions={true} />
          ))}
        </div>
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    </div>
  );
};

// Match Card Skeleton
export const MatchCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <Skeleton variant="text" className="w-32 h-6" />
        <Skeleton variant="rectangular" className="w-16 h-6" />
      </div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <Skeleton variant="text" className="w-40 h-8 mb-2" />
          <Skeleton variant="text" className="w-40 h-8" />
        </div>
        <Skeleton variant="text" className="w-12 h-12" />
      </div>
      <div className="grid grid-cols-3 gap-4 mt-4">
        <Skeleton variant="rectangular" className="h-10" />
        <Skeleton variant="rectangular" className="h-10" />
        <Skeleton variant="rectangular" className="h-10" />
      </div>
    </div>
  );
};