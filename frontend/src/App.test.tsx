import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Football Analytics app', () => {
  render(<App />);
  const titleElement = screen.getByText(/Football Analytics/i);
  expect(titleElement).toBeInTheDocument();
});

test('shows loading message', () => {
  render(<App />);
  const loadingElement = screen.getByText(/Loading advanced predictions/i);
  expect(loadingElement).toBeInTheDocument();
});
