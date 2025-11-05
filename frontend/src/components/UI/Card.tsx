import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  children: React.ReactNode;
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const cardVariants = {
  default: 'bg-bg-card border border-border-subtle',
  elevated: 'bg-bg-card border border-border-subtle shadow-lg',
  outlined: 'bg-bg-card border-2 border-border-primary',
  glass: 'bg-glass-bg backdrop-blur border border-glass-border',
};

const paddingVariants = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

export const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'lg',
  hover = false,
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        // Base styles
        'rounded-lg transition-all duration-200',
        // Variant styles
        cardVariants[variant],
        // Padding styles
        paddingVariants[padding],
        // Hover effects
        hover && 'hover:scale-[1.02] hover:shadow-xl hover:border-border-primary cursor-pointer',
        // Custom className
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardHeaderProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'flex flex-col space-y-1.5 pb-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardContent: React.FC<CardContentProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn('flex-1', className)}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardFooter: React.FC<CardFooterProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn(
        'flex items-center justify-between pt-4 border-t border-border-subtle',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

// Title component for card headers
interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
}

export const CardTitle: React.FC<CardTitleProps> = ({
  level = 3,
  className,
  children,
  ...props
}) => {
  const sizeClasses = {
    1: 'text-3xl font-bold',
    2: 'text-2xl font-bold',
    3: 'text-xl font-semibold',
    4: 'text-lg font-semibold',
    5: 'text-base font-medium',
    6: 'text-sm font-medium',
  };

  const commonProps = {
    className: cn(
      'text-text-primary leading-tight',
      sizeClasses[level],
      className
    ),
    ...props
  };

  if (level === 1) return <h1 {...commonProps}>{children}</h1>;
  if (level === 2) return <h2 {...commonProps}>{children}</h2>;
  if (level === 3) return <h3 {...commonProps}>{children}</h3>;
  if (level === 4) return <h4 {...commonProps}>{children}</h4>;
  if (level === 5) return <h5 {...commonProps}>{children}</h5>;
  return <h6 {...commonProps}>{children}</h6>;
};

// Description component for card headers
interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

export const CardDescription: React.FC<CardDescriptionProps> = ({
  className,
  children,
  ...props
}) => {
  return (
    <p
      className={cn(
        'text-text-secondary text-sm leading-relaxed',
        className
      )}
      {...props}
    >
      {children}
    </p>
  );
};

export default Card;