import axios from 'axios';
import type { Employee, Department, Position } from '../types';

const BASE = import.meta.env.VITE_EMPLOYEE_API_URL ?? 'http://localhost:8002/api/v1';

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

export interface EmployeeCreatePayload {
  user_id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  date_of_birth?: string;
  gender?: string;
  employment_type: string;
  hire_date: string;
  department_id?: string;
  position_id?: string;
  manager_id?: string;
}

export type EmployeeUpdatePayload = Partial<
  Omit<EmployeeCreatePayload, 'user_id' | 'employee_code'>
>;

// Employees
export const createEmployee = (data: EmployeeCreatePayload) =>
  client.post<Employee>('/employees/', data);
export const employeeSignUp = (data: Omit<EmployeeCreatePayload, 'user_id'>) =>
  client.post<Employee>('/employees/sign-up', data);
export const getEmployees = (params?: Record<string, string | number>) =>
  client.get<Employee[]>('/employees/', { params });
export const getEmployee = (id: string) => client.get<Employee>(`/employees/${id}`);
export const updateEmployee = (id: string, data: EmployeeUpdatePayload) =>
  client.patch<Employee>(`/employees/${id}`, data);
export const terminateEmployee = (
  id: string,
  data: { employee_id: string; reason: string; termination_date: string },
) => client.post<Employee>(`/employees/${id}/terminate`, data);
export const getMyProfile = () => client.get<Employee>('/employees/me/profile');

// Departments
export const getDepartments = () => client.get<Department[]>('/departments/departments');
export const createDepartment = (data: { name: string; description?: string }) =>
  client.post<Department>('/departments/departments', data);
export const updateDepartment = (id: string, data: Partial<Department>) =>
  client.patch<Department>(`/departments/departments/${id}`, data);

// Positions
export const getPositions = (params?: Record<string, string>) =>
  client.get<Position[]>('/positions/positions', { params });
export const createPosition = (data: {
  name: string;
  description?: string;
  level?: string;
  department_id?: string;
}) => client.post<Position>('/positions/positions', data);
