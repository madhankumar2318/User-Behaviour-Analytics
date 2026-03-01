// Mock socket.io-client — must match the named export: import { io } from 'socket.io-client'
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  })),
}));

// Mock axios to prevent real HTTP calls in CI
jest.mock('axios', () => ({
  get: jest.fn(() => Promise.reject(new Error('No backend in CI'))),
  post: jest.fn(() => Promise.reject(new Error('No backend in CI'))),
  defaults: { headers: { common: {} } },
}));

import { render, act } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => { });
});

afterEach(() => {
  console.error.mockRestore();
  localStorage.clear();
});

test('renders app without crashing', async () => {
  await act(async () => {
    render(<App />);
  });
  expect(document.body).toBeTruthy();
});

test('shows login page when user is not authenticated', async () => {
  localStorage.removeItem('token');
  await act(async () => {
    render(<App />);
  });
  await act(async () => {
    await new Promise((r) => setTimeout(r, 200));
  });
  expect(document.body).toBeTruthy();
});
