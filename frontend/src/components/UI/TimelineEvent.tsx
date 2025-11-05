import React from 'react';
import { motion } from 'framer-motion';

interface TimelineEventProps {
  time: string;
  title: string;
  description?: string;
  type: 'goal' | 'card' | 'substitution' | 'corner' | 'foul' | 'offside' | 'penalty' | 'other';
  team: 'home' | 'away';
  player?: string;
  isLive?: boolean;
  className?: string;
}

export const TimelineEvent: React.FC<TimelineEventProps> = ({
  time,
  title,
  description,
  type,
  team,
  player,
  isLive = false,
  className = ''
}) => {
  const getEventConfig = () => {
    switch (type) {
      case 'goal':
        return {
          icon: '⚽',
          color: 'text-green-400',
          bgColor: 'bg-green-900/20',
          borderColor: 'border-green-500/30'
        };
      case 'card':
        return {
          icon: '🟨',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900/20',
          borderColor: 'border-yellow-500/30'
        };
      case 'substitution':
        return {
          icon: '🔄',
          color: 'text-blue-400',
          bgColor: 'bg-blue-900/20',
          borderColor: 'border-blue-500/30'
        };
      case 'corner':
        return {
          icon: '🚩',
          color: 'text-purple-400',
          bgColor: 'bg-purple-900/20',
          borderColor: 'border-purple-500/30'
        };
      case 'foul':
        return {
          icon: '⚠️',
          color: 'text-orange-400',
          bgColor: 'bg-orange-900/20',
          borderColor: 'border-orange-500/30'
        };
      case 'offside':
        return {
          icon: '🚫',
          color: 'text-red-400',
          bgColor: 'bg-red-900/20',
          borderColor: 'border-red-500/30'
        };
      case 'penalty':
        return {
          icon: '🥅',
          color: 'text-pink-400',
          bgColor: 'bg-pink-900/20',
          borderColor: 'border-pink-500/30'
        };
      default:
        return {
          icon: '📝',
          color: 'text-gray-400',
          bgColor: 'bg-gray-900/20',
          borderColor: 'border-gray-500/30'
        };
    }
  };

  const eventConfig = getEventConfig();

  return (
    <motion.div
      initial={{ opacity: 0, x: team === 'home' ? -20 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      className={`
        flex items-start gap-3 p-4 rounded-lg border transition-all
        ${eventConfig.bgColor} ${eventConfig.borderColor}
        ${team === 'home' ? 'flex-row' : 'flex-row-reverse'}
        ${isLive ? 'ring-2 ring-primary-500/50' : ''}
        hover:border-primary-500/50 hover:bg-primary-900/10
        ${className}
      `}
    >
      {/* Time Badge */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className={`
          flex-shrink-0 flex items-center justify-center
          w-12 h-8 rounded-md font-mono text-sm font-bold
          ${eventConfig.color} ${eventConfig.bgColor}
          border ${eventConfig.borderColor}
          ${isLive ? 'animate-pulse' : ''}
        `}
      >
        {time}'
      </motion.div>

      {/* Event Icon */}
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="flex-shrink-0 text-xl"
      >
        {eventConfig.icon}
      </motion.div>

      {/* Event Content */}
      <div className={`flex-1 ${team === 'away' ? 'text-right' : 'text-left'}`}>
        <motion.h4
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.3 }}
          className={`font-semibold ${eventConfig.color} mb-1`}
        >
          {title}
        </motion.h4>

        {player && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.3 }}
            className="text-text-primary text-sm font-medium mb-1"
          >
            {player}
          </motion.p>
        )}

        {description && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.3 }}
            className="text-text-secondary text-xs"
          >
            {description}
          </motion.p>
        )}

        {/* Live Indicator */}
        {isLive && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="flex items-center gap-1 mt-2"
          >
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-red-400 text-xs font-medium uppercase tracking-wider">
              Acontecendo agora
            </span>
          </motion.div>
        )}
      </div>

      {/* Team Side Indicator */}
      <div
        className={`
          absolute ${team === 'home' ? 'left-0' : 'right-0'} top-0 bottom-0
          w-1 rounded-l-lg ${team === 'home' ? 'bg-primary-500' : 'bg-accent-500'}
          ${isLive ? 'animate-pulse' : ''}
        `}
      />
    </motion.div>
  );
};

export default TimelineEvent;