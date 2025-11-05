/**
 * Utility function for combining CSS classes
 * Simple implementation of clsx/cn
 */
export const cn = (...classes: (string | undefined | null | false)[]) => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Format percentage with proper decimal places
 */
export const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

/**
 * Format confidence level with color coding
 */
export const getConfidenceLevel = (confidence: number): { level: string; color: string } => {
  if (confidence >= 0.8) {
    return { level: 'Muito Alta', color: 'text-primary-400' };
  } else if (confidence >= 0.7) {
    return { level: 'Alta', color: 'text-accent-400' };
  } else if (confidence >= 0.6) {
    return { level: 'Média', color: 'text-warning-400' };
  } else {
    return { level: 'Baixa', color: 'text-red-400' };
  }
};

/**
 * Format odds value
 */
export const formatOdds = (odds: number): string => {
  return odds.toFixed(2);
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

/**
 * Format date for display
 */
export const formatDate = (date: string | Date): string => {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(date));
};

/**
 * Format time for display
 */
export const formatTime = (date: string | Date): string => {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
};

/**
 * Sleep function for delays
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Debounce function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Generate random ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};