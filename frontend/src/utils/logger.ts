/**
 * Logger utilitário para desenvolvimento e debug
 * Pode ser desabilitado em produção através da variável de ambiente
 */

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
  /**
   * Log informativo (azul)
   */
  info: (module: string, message: string, ...args: any[]) => {
    if (isDevelopment) {
      console.log(
        `%c[${module}]%c ${message}`,
        'color: #3b82f6; font-weight: bold',
        'color: inherit',
        ...args
      );
    }
  },

  /**
   * Log de warning (amarelo)
   */
  warn: (module: string, message: string, ...args: any[]) => {
    if (isDevelopment) {
      console.warn(
        `%c[${module}]%c ${message}`,
        'color: #f59e0b; font-weight: bold',
        'color: inherit',
        ...args
      );
    }
  },

  /**
   * Log de erro (vermelho) - sempre ativo
   */
  error: (module: string, message: string, ...args: any[]) => {
    console.error(
      `%c[${module}]%c ${message}`,
      'color: #ef4444; font-weight: bold',
      'color: inherit',
      ...args
    );
  },

  /**
   * Log de sucesso (verde)
   */
  success: (module: string, message: string, ...args: any[]) => {
    if (isDevelopment) {
      console.log(
        `%c[${module}]%c ✅ ${message}`,
        'color: #10b981; font-weight: bold',
        'color: inherit',
        ...args
      );
    }
  },

  /**
   * Log de API call (roxo)
   */
  api: (method: string, endpoint: string, data?: any) => {
    if (isDevelopment) {
      console.log(
        `%c[API]%c ${method} ${endpoint}`,
        'color: #8b5cf6; font-weight: bold',
        'color: inherit',
        data ? data : ''
      );
    }
  },

  /**
   * Log de timing/performance
   */
  time: (label: string) => {
    if (isDevelopment) {
      console.time(`⏱️ ${label}`);
    }
  },

  timeEnd: (label: string) => {
    if (isDevelopment) {
      console.timeEnd(`⏱️ ${label}`);
    }
  },

  /**
   * Agrupa logs relacionados
   */
  group: (label: string) => {
    if (isDevelopment) {
      console.group(label);
    }
  },

  groupEnd: () => {
    if (isDevelopment) {
      console.groupEnd();
    }
  },

  /**
   * Log de tabela (útil para arrays de objetos)
   */
  table: (data: any) => {
    if (isDevelopment) {
      console.table(data);
    }
  }
};
