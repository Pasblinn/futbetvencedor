import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface NotificationToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'prediction_ready';
  title: string;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onClose,
  position = 'top-right',
  action
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    // Progress bar animation
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (duration / 100));
        return newProgress <= 0 ? 0 : newProgress;
      });
    }, 100);

    return () => {
      clearTimeout(timer);
      clearInterval(progressTimer);
    };
  }, [duration]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onClose(id), 300);
  };

  const getTypeConfig = () => {
    switch (type) {
      case 'success':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ),
          bgColor: 'bg-green-900/90',
          borderColor: 'border-green-500/50',
          textColor: 'text-green-100',
          iconColor: 'text-green-400',
          progressColor: 'bg-green-400'
        };
      case 'error':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          bgColor: 'bg-red-900/90',
          borderColor: 'border-red-500/50',
          textColor: 'text-red-100',
          iconColor: 'text-red-400',
          progressColor: 'bg-red-400'
        };
      case 'warning':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          ),
          bgColor: 'bg-yellow-900/90',
          borderColor: 'border-yellow-500/50',
          textColor: 'text-yellow-100',
          iconColor: 'text-yellow-400',
          progressColor: 'bg-yellow-400'
        };
      case 'info':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          bgColor: 'bg-blue-900/90',
          borderColor: 'border-blue-500/50',
          textColor: 'text-blue-100',
          iconColor: 'text-blue-400',
          progressColor: 'bg-blue-400'
        };
      case 'prediction_ready':
        return {
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          ),
          bgColor: 'bg-primary-900/90',
          borderColor: 'border-primary-500/50',
          textColor: 'text-primary-100',
          iconColor: 'text-primary-400',
          progressColor: 'bg-primary-400'
        };
      default:
        return {
          icon: null,
          bgColor: 'bg-gray-900/90',
          borderColor: 'border-gray-500/50',
          textColor: 'text-gray-100',
          iconColor: 'text-gray-400',
          progressColor: 'bg-gray-400'
        };
    }
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      default:
        return 'top-4 right-4';
    }
  };

  const getAnimationDirection = () => {
    if (position.includes('right')) return { x: 400 };
    if (position.includes('left')) return { x: -400 };
    return { y: -100 };
  };

  const config = getTypeConfig();

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ ...getAnimationDirection(), opacity: 0, scale: 0.8 }}
          animate={{ x: 0, y: 0, opacity: 1, scale: 1 }}
          exit={{ ...getAnimationDirection(), opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className={`
            fixed ${getPositionClasses()} z-toast
            w-80 max-w-sm rounded-lg border backdrop-blur-md
            ${config.bgColor} ${config.borderColor}
            shadow-xl overflow-hidden
          `}
        >
          {/* Progress Bar */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gray-700/50">
            <motion.div
              className={`h-full ${config.progressColor}`}
              initial={{ width: '100%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>

          <div className="p-4">
            <div className="flex items-start gap-3">
              {/* Icon */}
              {config.icon && (
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                  className={`flex-shrink-0 ${config.iconColor}`}
                >
                  {config.icon}
                </motion.div>
              )}

              {/* Content */}
              <div className="flex-1">
                <motion.h4
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15, duration: 0.2 }}
                  className={`font-semibold ${config.textColor} mb-1`}
                >
                  {title}
                </motion.h4>

                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2, duration: 0.2 }}
                  className={`text-sm ${config.textColor} opacity-90`}
                >
                  {message}
                </motion.p>

                {/* Action Button */}
                {action && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3, duration: 0.2 }}
                    onClick={action.onClick}
                    className={`
                      mt-3 px-3 py-1.5 rounded-md text-xs font-medium
                      bg-white/10 hover:bg-white/20 transition-colors
                      ${config.textColor}
                    `}
                  >
                    {action.label}
                  </motion.button>
                )}
              </div>

              {/* Close Button */}
              <motion.button
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.25, duration: 0.2 }}
                onClick={handleClose}
                className={`
                  flex-shrink-0 p-1 rounded-md transition-colors
                  ${config.textColor} hover:bg-white/10
                `}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </motion.button>
            </div>
          </div>

          {/* Hover pause effect */}
          <div
            className="absolute inset-0 cursor-pointer"
            onMouseEnter={() => setProgress(progress)}
            onMouseLeave={() => {}}
            onClick={handleClose}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default NotificationToast;