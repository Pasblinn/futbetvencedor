import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Brain, Trophy } from 'lucide-react';
import { useTranslation } from '../../contexts/I18nContext';

interface PredictionModesHeaderProps {
  activeMode: 'automatic' | 'assisted' | 'manual';
  onModeChange: (mode: 'automatic' | 'assisted' | 'manual') => void;
}

export const PredictionModesHeader: React.FC<PredictionModesHeaderProps> = ({
  activeMode,
  onModeChange
}) => {
  const { t } = useTranslation();

  const modes = [
    {
      id: 'automatic' as const,
      nameKey: 'predictions.modes.automatic',
      icon: Bot,
      color: 'from-blue-600 to-blue-700',
      descriptionKey: 'predictions.modes.automatic_desc',
      difficultyKey: 'predictions.modes.beginner'
    },
    {
      id: 'assisted' as const,
      nameKey: 'predictions.modes.assisted',
      icon: Brain,
      color: 'from-purple-600 to-purple-700',
      descriptionKey: 'predictions.modes.assisted_desc',
      difficultyKey: 'predictions.modes.intermediate'
    },
    {
      id: 'manual' as const,
      nameKey: 'predictions.modes.expert',
      icon: Trophy,
      color: 'from-yellow-600 to-yellow-700',
      descriptionKey: 'predictions.modes.expert_desc',
      difficultyKey: 'predictions.modes.advanced'
    }
  ];

  return (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 mb-6 shadow-2xl border border-slate-700">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">
          🎯 {t('predictions.modes.create_title')}
        </h2>
        <p className="text-slate-400 text-sm">
          {t('predictions.modes.create_subtitle')}
        </p>
      </div>

      {/* Mode Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isActive = activeMode === mode.id;

          return (
            <motion.button
              key={mode.id}
              onClick={() => onModeChange(mode.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`
                relative p-6 rounded-xl border-2 transition-all duration-300
                ${isActive
                  ? 'border-white bg-gradient-to-br ' + mode.color + ' shadow-xl'
                  : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                }
              `}
            >
              {/* Active Indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeMode"
                  className="absolute inset-0 bg-white/10 rounded-xl"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}

              <div className="relative z-10">
                {/* Icon */}
                <div className={`
                  inline-flex p-3 rounded-lg mb-4
                  ${isActive ? 'bg-white/20' : 'bg-slate-700'}
                `}>
                  <Icon className={`w-6 h-6 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                </div>

                {/* Title */}
                <h3 className={`text-xl font-bold mb-2 ${isActive ? 'text-white' : 'text-slate-300'}`}>
                  {t(mode.nameKey)}
                </h3>

                {/* Description */}
                <p className={`text-sm mb-3 ${isActive ? 'text-white/80' : 'text-slate-400'}`}>
                  {t(mode.descriptionKey)}
                </p>

                {/* Difficulty Badge */}
                <div className={`
                  inline-block px-3 py-1 rounded-full text-xs font-semibold
                  ${isActive ? 'bg-white/20 text-white' : 'bg-slate-700 text-slate-400'}
                `}>
                  {t(mode.difficultyKey)}
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Mode Description */}
      <motion.div
        key={activeMode}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-6 p-4 bg-slate-700/30 rounded-lg border border-slate-600"
      >
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
          <div>
            <p className="text-white text-sm font-medium mb-1">
              {activeMode === 'automatic' && t('predictions.modes.how_automatic')}
              {activeMode === 'assisted' && t('predictions.modes.how_assisted')}
              {activeMode === 'manual' && t('predictions.modes.how_expert')}
            </p>
            <p className="text-slate-400 text-xs leading-relaxed">
              {activeMode === 'automatic' && (
                <>
                  {t('predictions.modes.automatic_explain')}
                  <br />
                  <span className="text-blue-400">✓ {t('predictions.modes.automatic_benefit1')}</span> •{' '}
                  <span className="text-blue-400">✓ {t('predictions.modes.automatic_benefit2')}</span> •{' '}
                  <span className="text-blue-400">✓ {t('predictions.modes.automatic_benefit3')}</span>
                </>
              )}
              {activeMode === 'assisted' && (
                <>
                  {t('predictions.modes.assisted_explain')}
                  <br />
                  <span className="text-purple-400">✓ {t('predictions.modes.assisted_benefit1')}</span> •{' '}
                  <span className="text-purple-400">✓ {t('predictions.modes.assisted_benefit2')}</span> •{' '}
                  <span className="text-purple-400">✓ {t('predictions.modes.assisted_benefit3')}</span>
                </>
              )}
              {activeMode === 'manual' && (
                <>
                  {t('predictions.modes.expert_explain')}
                  <br />
                  <span className="text-yellow-400">✓ {t('predictions.modes.expert_benefit1')}</span> •{' '}
                  <span className="text-yellow-400">✓ {t('predictions.modes.expert_benefit2')}</span> •{' '}
                  <span className="text-yellow-400">✓ {t('predictions.modes.expert_benefit3')}</span>
                </>
              )}
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
