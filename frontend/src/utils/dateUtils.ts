// Date formatting utilities for consistent date/time display
import { logger } from './logger';

/**
 * Valida se uma data é válida
 */
const isValidDate = (date: Date): boolean => {
  return date instanceof Date && !isNaN(date.getTime());
};

/**
 * Converte string para Date com validação
 */
const parseDate = (dateStr: string | null | undefined): Date | null => {
  if (!dateStr) {
    logger.warn('dateUtils', 'Received null/undefined date string');
    return null;
  }

  try {
    const date = new Date(dateStr);
    if (!isValidDate(date)) {
      logger.warn('dateUtils', 'Invalid date string:', dateStr);
      return null;
    }
    return date;
  } catch (error) {
    logger.error('dateUtils', 'Error parsing date:', dateStr, error);
    return null;
  }
};

export const formatMatchDateTime = (dateStr: string | null | undefined): string => {
  const date = parseDate(dateStr);

  if (!date) return 'Data indisponível';

  // Brazilian format: DD/MM/YYYY HH:MM
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/Sao_Paulo' // Forçar timezone BRT
  });
};

export const formatMatchTime = (dateStr: string | null | undefined): string => {
  const date = parseDate(dateStr);

  if (!date) return '--:--';

  // Just time: HH:MM
  return date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/Sao_Paulo'
  });
};

export const formatMatchDate = (dateStr: string | null | undefined): string => {
  const date = parseDate(dateStr);

  if (!date) return '--/--/----';

  // Just date: DD/MM/YYYY
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'America/Sao_Paulo'
  });
};

export const formatMatchDateShort = (dateStr: string | null | undefined): string => {
  const date = parseDate(dateStr);

  if (!date) return '--/--/--';

  // Short date: DD/MM/YY
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    timeZone: 'America/Sao_Paulo'
  });
};

export const isToday = (dateStr: string | null | undefined): boolean => {
  const date = parseDate(dateStr);
  if (!date) return false;

  const today = new Date();
  return date.toDateString() === today.toDateString();
};

export const isTomorrow = (dateStr: string | null | undefined): boolean => {
  const date = parseDate(dateStr);
  if (!date) return false;

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return date.toDateString() === tomorrow.toDateString();
};

export const getRelativeDateString = (dateStr: string | null | undefined): string => {
  if (!dateStr) return 'Data indisponível';

  if (isToday(dateStr)) {
    return `Hoje, ${formatMatchTime(dateStr)}`;
  } else if (isTomorrow(dateStr)) {
    return `Amanhã, ${formatMatchTime(dateStr)}`;
  } else {
    return formatMatchDateTime(dateStr);
  }
};