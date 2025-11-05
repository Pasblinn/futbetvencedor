import React from 'react';
import { motion } from 'framer-motion';

interface OddsDisplayProps {
  odds: number;
  previousOdds?: number;
  market?: string;
  selection?: string;
  isUpdating?: boolean;
  showArrow?: boolean;
  className?: string;
}

export const OddsDisplay: React.FC<OddsDisplayProps> = ({
  odds,
  previousOdds,
  market,
  selection,
  isUpdating = false,
  showArrow = true,
  className = ''
}) => {
  const getTrend = () => {
    if (!previousOdds || previousOdds === odds) return 'stable';
    return odds > previousOdds ? 'up' : 'down';
  };

  const getTrendColor = () => {
    const trend = getTrend();
    switch (trend) {
      case 'up': return 'text-red-400 border-red-400/30 bg-red-900/20'; // Odds subindo = pior para apostador
      case 'down': return 'text-green-400 border-green-400/30 bg-green-900/20'; // Odds descendo = melhor para apostador
      default: return 'text-gray-400 border-gray-400/30 bg-gray-900/20';
    }
  };

  const getTrendIcon = () => {
    const trend = getTrend();
    if (!showArrow || trend === 'stable') return null;

    const icons = {
      up: (
        <motion.svg
          initial={{ y: 2, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="w-3 h-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M7 17l9.2-9.2M17 17V8" />
        </motion.svg>
      ),
      down: (
        <motion.svg
          initial={{ y: -2, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="w-3 h-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M17 7l-9.2 9.2M7 7v9" />
        </motion.svg>
      )
    };

    return icons[trend];
  };

  const formatOdds = (value: number) => {
    return value.toFixed(2);
  };

  return (
    <motion.div
      initial={{ scale: 0.95 }}
      animate={{
        scale: isUpdating ? [1, 1.05, 1] : 1,
        borderColor: isUpdating ? ['rgba(16, 185, 129, 0.3)', 'rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.3)'] : undefined
      }}
      transition={{
        scale: { duration: 0.3 },
        borderColor: isUpdating ? { duration: 1, repeat: Infinity } : undefined
      }}
      className={`
        inline-flex items-center gap-2 px-3 py-2 rounded-lg border
        font-mono text-sm font-semibold transition-all
        ${getTrendColor()}
        ${isUpdating ? 'ring-2 ring-primary-500/50' : ''}
        ${className}
      `}
    >
      {/* Ícone de tendência */}
      <div className="flex items-center">
        {getTrendIcon()}
      </div>

      {/* Valor das odds */}
      <motion.span
        key={odds}
        initial={{ scale: 1.1, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.2 }}
        className="text-base font-bold"
      >
        {formatOdds(odds)}
      </motion.span>

      {/* Indicador de atualização */}
      {isUpdating && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-3 h-3"
        >
          <svg className="w-full h-full text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </motion.div>
      )}

      {/* Tooltip com informações adicionais */}
      {(market || selection) && (
        <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap z-10">
          {market && selection ? `${market}: ${selection}` : market || selection}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </motion.div>
  );
};

export default OddsDisplay;