import React from 'react';
import { motion } from 'framer-motion';

interface LiveBadgeProps {
  status: 'live' | 'upcoming' | 'finished' | 'halftime' | 'delayed';
  minute?: number;
  className?: string;
}

export const LiveBadge: React.FC<LiveBadgeProps> = ({
  status,
  minute,
  className = ''
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'live':
        return {
          text: minute ? `${minute}'` : 'AO VIVO',
          bgColor: 'bg-red-600',
          textColor: 'text-white',
          animate: true,
          icon: '🔴'
        };
      case 'halftime':
        return {
          text: 'INTERVALO',
          bgColor: 'bg-accent-600',
          textColor: 'text-white',
          animate: false,
          icon: '⏸️'
        };
      case 'upcoming':
        return {
          text: 'FUTURO',
          bgColor: 'bg-primary-600',
          textColor: 'text-white',
          animate: false,
          icon: '⏰'
        };
      case 'finished':
        return {
          text: 'FINAL',
          bgColor: 'bg-gray-600',
          textColor: 'text-white',
          animate: false,
          icon: '✅'
        };
      case 'delayed':
        return {
          text: 'ADIADO',
          bgColor: 'bg-warning-600',
          textColor: 'text-white',
          animate: true,
          icon: '⚠️'
        };
      default:
        return {
          text: 'N/A',
          bgColor: 'bg-gray-600',
          textColor: 'text-white',
          animate: false,
          icon: ''
        };
    }
  };

  const config = getStatusConfig();

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{
        scale: 1,
        opacity: 1,
        boxShadow: config.animate
          ? ['0 0 0 0 rgba(239, 68, 68, 0.7)', '0 0 0 10px rgba(239, 68, 68, 0)', '0 0 0 0 rgba(239, 68, 68, 0.7)']
          : undefined
      }}
      transition={{
        duration: 0.3,
        boxShadow: config.animate ? {
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut'
        } : undefined
      }}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold
        uppercase tracking-wider ${config.bgColor} ${config.textColor}
        ${config.animate ? 'animate-pulse' : ''}
        ${className}
      `}
    >
      <span className="text-xs">{config.icon}</span>
      <span>{config.text}</span>
      {config.animate && (
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
          className="w-2 h-2 bg-white rounded-full"
        />
      )}
    </motion.div>
  );
};

export default LiveBadge;