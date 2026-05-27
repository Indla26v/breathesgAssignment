import { apiClient } from './client';
import { User } from '../types';

export const login = async (email: string, password: string): Promise<User> => {
  const response = await apiClient.post('auth/token/', { email, password });
  return response.data.data.user;
};

export const logout = async (): Promise<void> => {
  await apiClient.post('auth/logout/');
};

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get('auth/me/');
  return response.data.data;
};
