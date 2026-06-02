import axios from 'axios';
import type { User, Role, Permission, TokenResponse } from '../types';

const BASE = import.meta.env.VITE_AUTH_API_URL ?? 'http://localhost:8001/api/v1';

export const client = axios.create({ baseURL: BASE });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err: unknown) => {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(err);
  },
);

// Auth
export const signUp = (data: { username: string; email: string; password: string }) =>
  client.post<TokenResponse>('/auth/sign-up', data);

export const signIn = (data: { username: string; password: string }) => {
  const form = new URLSearchParams();
  form.append('username', data.username);
  form.append('password', data.password);
  return client.post<TokenResponse>('/auth/sign-in', form);
};

export const forgotPassword = (data: { email: string }) =>
  client.post('/auth/forgot-password', data);

export const resetPassword = (data: { email: string; otp_code: string; new_password: string }) =>
  client.post('/auth/reset-password', data);

export const changePassword = (data: { current_password: string; new_password: string }) =>
  client.post('/auth/change-password', data);

// Users
export const getMe = () => client.get<User>('/users/me');
export const updateMe = (data: Partial<Pick<User, 'username' | 'email'>>) =>
  client.patch<User>('/users/me', data);
export const getUsers = () => client.get<User[]>('/users/');
export const getAdmins = () => client.get<User[]>('/users/admins');
export const createUser = (data: {
  username: string;
  email: string;
  password: string;
  is_superuser: boolean;
}) => client.post<User>('/users/create-user', data);
export const getUser = (id: string) => client.get<User>(`/users/${id}`);
export const updateUser = (id: string, data: Partial<User>) =>
  client.patch<User>(`/users/${id}`, data);

// Roles
export const getRoles = () => client.get<Role[]>('/roles/');
export const createRole = (data: { name: string; description?: string }) =>
  client.post<Role>('/roles/', data);
export const getRole = (id: string) => client.get<Role>(`/roles/${id}`);
export const assignRole = (data: { user_id: string; role_id: string }) =>
  client.post('/roles/assign-role-to-user', data);
export const removeRole = (userId: string, roleId: string) =>
  client.delete(`/roles/${userId}/roles/${roleId}`);

// Permissions
export const getPermissions = () => client.get<Permission[]>('/permissions/');
export const createPermission = (data: {
  resource: string;
  action: string;
  description?: string;
}) => client.post<Permission>('/permissions/', data);
export const getUserPermissions = (userId: string) =>
  client.get(`/permissions/user-permissions/${userId}`);
export const assignPermToRole = (data: { role_id: string; permission_id: string }) =>
  client.post('/permissions/assign-permission-to-role', data);
export const removePermFromRole = (roleId: string, permId: string) =>
  client.delete(`/permissions/remove-permission-from-role/${roleId}/${permId}`);
export const grantPermToUser = (data: { user_id: string; permission_id: string }) =>
  client.post('/permissions/grant-permission-to-user', data);
export const removePermFromUser = (userId: string, permId: string) =>
  client.delete(`/permissions/remove-permission-from-user/${userId}/${permId}`);
