import React, { useEffect, useRef, memo } from 'react';
import { motion } from 'framer-motion';
import { CountUp } from 'countup.js';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'error';
  isAnimated?: boolean;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'primary',
  isAnimated = true,
  className = ''
}) => {
  const countRef = useRef<HTMLDivElement>(null);
  const countUpRef = useRef<CountUp | null>(null);

  useEffect(() => {
    if (isAnimated && countRef.current && typeof value === 'number') {
      if (countUpRef.current) {
        countUpRef.current.update(value);
      } else {
        countUpRef.current = new CountUp(countRef.current, value, {
          duration: 2,
          useEasing: true,
          useGrouping: true,
          separator: '.',
          decimal: ','
        });

        if (!countUpRef.current.error) {
          countUpRef.current.start();
        }
      }
    }
  }, [value, isAnimated]);

  const getColorClasses = () => {
    const base = 'bg-bg-card shadow-sm hover:shadow-md';
    switch (color) {
      case 'accent':
        return `${base} border-accent-500/20 hover:border-accent-500/40`;
      case 'success':
        return `${base} border-success-500/20 hover:border-success-500/40`;
      case 'warning':
        return `${base} border-warning-500/20 hover:border-warning-500/40`;
      case 'error':
        return `${base} border-red-500/20 hover:border-red-500/40`;
      default:
        return `${base} border-primary-500/20 hover:border-primary-500/40`;
    }
  };

  const getTrendIcon = () => {
    if (!trend) return null;

    const icons = {
      up: (
        <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V8m0 0H8" />
        </svg>
      ),
      down: (
        <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v9m0 0h9" />
        </svg>
      ),
      stable: (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      )
    };

    return icons[trend];
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-primary-400';
      case 'down': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`p-6 rounded-lg border transition-all duration-300 hover:transform hover:-translate-y-1 ${getColorClasses()} ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {icon && (
              <div className={`p-2 rounded-lg ${
                color === 'accent' ? 'bg-accent-600/20' : 'bg-primary-600/20'
              }`}>
                {icon}
              </div>
            )}
            <h3 className="text-text-secondary text-sm font-medium uppercase tracking-wider">
              {title}
            </h3>
          </div>

          <div className="mb-2">
            {isAnimated && typeof value === 'number' ? (
              <div
                ref={countRef}
                className="text-3xl font-bold text-text-primary font-mono"
              />
            ) : (
              <div className="text-3xl font-bold text-text-primary font-mono">
                {value}
              </div>
            )}
          </div>

          {subtitle && (
            <p className="text-text-tertiary text-sm">
              {subtitle}
            </p>
          )}
        </div>

        {(trend || trendValue !== undefined) && (
          <div className="flex items-center gap-1 ml-4">
            {getTrendIcon()}
            {trendValue !== undefined && (
              <span className={`text-sm font-medium ${getTrendColor()}`}>
                {trendValue > 0 && '+'}
                {trendValue}%
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default memo(StatCard);