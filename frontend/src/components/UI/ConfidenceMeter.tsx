import React from 'react';
import { motion } from 'framer-motion';

interface ConfidenceMeterProps {
  confidence: number; // 0-100
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showPercentage?: boolean;
  label?: string;
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'error';
  animated?: boolean;
  className?: string;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  size = 'md',
  showPercentage = true,
  label,
  color = 'primary',
  animated = true,
  className = ''
}) => {
  const getSizeConfig = () => {
    switch (size) {
      case 'sm':
        return { container: 'w-12 h-12', inner: 'w-8 h-8', text: 'text-xs', strokeWidth: 6 };
      case 'md':
        return { container: 'w-16 h-16', inner: 'w-12 h-12', text: 'text-sm', strokeWidth: 8 };
      case 'lg':
        return { container: 'w-20 h-20', inner: 'w-16 h-16', text: 'text-base', strokeWidth: 10 };
      case 'xl':
        return { container: 'w-24 h-24', inner: 'w-20 h-20', text: 'text-lg', strokeWidth: 12 };
      default:
        return { container: 'w-16 h-16', inner: 'w-12 h-12', text: 'text-sm', strokeWidth: 8 };
    }
  };

  const getColorConfig = () => {
    switch (color) {
      case 'accent':
        return {
          primary: '#f59e0b',
          secondary: 'rgb(245, 158, 11)',
          glow: 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.5))'
        };
      case 'success':
        return {
          primary: '#10b981',
          secondary: 'rgb(16, 185, 129)',
          glow: 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.5))'
        };
      case 'warning':
        return {
          primary: '#f59e0b',
          secondary: 'rgb(245, 158, 11)',
          glow: 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.5))'
        };
      case 'error':
        return {
          primary: '#ef4444',
          secondary: 'rgb(239, 68, 68)',
          glow: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.5))'
        };
      default:
        return {
          primary: '#10b981',
          secondary: 'rgb(16, 185, 129)',
          glow: 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.5))'
        };
    }
  };

  const sizeConfig = getSizeConfig();
  const colorConfig = getColorConfig();

  // Normalizar confiança para 0-100
  const normalizedConfidence = Math.min(100, Math.max(0, confidence));

  // Calcular o ângulo para o SVG (0-360 graus)
  const angle = (normalizedConfidence / 100) * 360;

  // Configurações do círculo SVG
  const center = 50;
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (normalizedConfidence / 100) * circumference;

  const getConfidenceLevel = () => {
    if (normalizedConfidence >= 80) return { level: 'Excelente', color: 'text-green-400' };
    if (normalizedConfidence >= 65) return { level: 'Boa', color: 'text-primary-400' };
    if (normalizedConfidence >= 50) return { level: 'Moderada', color: 'text-accent-400' };
    if (normalizedConfidence >= 35) return { level: 'Baixa', color: 'text-orange-400' };
    return { level: 'Muito Baixa', color: 'text-red-400' };
  };

  const confidenceLevel = getConfidenceLevel();

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      {label && (
        <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          {label}
        </span>
      )}

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className={`relative ${sizeConfig.container} flex items-center justify-center`}
      >
        {/* Background Circle */}
        <svg
          className="absolute inset-0 transform -rotate-90"
          width="100%"
          height="100%"
          viewBox="0 0 100 100"
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgb(51, 65, 85)"
            strokeWidth={sizeConfig.strokeWidth * 0.6}
          />
        </svg>

        {/* Progress Circle */}
        <svg
          className="absolute inset-0 transform -rotate-90"
          width="100%"
          height="100%"
          viewBox="0 0 100 100"
          style={{ filter: colorConfig.glow }}
        >
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={colorConfig.primary}
            strokeWidth={sizeConfig.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            initial={{ strokeDashoffset: circumference }}
            animate={{
              strokeDashoffset: animated ? strokeDashoffset : strokeDashoffset
            }}
            transition={{
              duration: animated ? 1.5 : 0,
              ease: "easeOut",
              delay: 0.2
            }}
          />
        </svg>

        {/* Center Content */}
        <div className="relative z-10 flex flex-col items-center justify-center">
          {showPercentage && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.5, duration: 0.3 }}
              className={`${sizeConfig.text} font-bold font-mono text-text-primary`}
            >
              {Math.round(normalizedConfidence)}%
            </motion.span>
          )}
        </div>

        {/* Glow Effect */}
        {animated && (
          <motion.div
            animate={{
              boxShadow: [
                `0 0 0 0 ${colorConfig.secondary}40`,
                `0 0 0 10px ${colorConfig.secondary}00`,
                `0 0 0 0 ${colorConfig.secondary}40`
              ]
            }}
            transition={{ duration: 2, repeat: Infinity }}
            className={`absolute inset-0 rounded-full`}
          />
        )}
      </motion.div>

      {/* Confidence Level Label */}
      <div className="text-center">
        <span className={`text-xs font-medium ${confidenceLevel.color}`}>
          {confidenceLevel.level}
        </span>
      </div>
    </div>
  );
};

export default ConfidenceMeter;