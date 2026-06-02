import axios from 'axios';
import type { EmployeeSalary, PayrollRecord, PaymentFrequencyEnum } from '../types';

const BASE = import.meta.env.VITE_PAYROLL_API_URL ?? 'http://localhost:8003/api/v1';

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

// Self-service
export const getMyPayroll = (params?: Record<string, string | number>) =>
  client.get<PayrollRecord[]>('/payroll/my-payroll', { params });
export const getMySalary = () => client.get<EmployeeSalary>('/payroll/my-salary');

// Admin — salaries
export const createSalary = (data: {
  employee_id: string;
  basic_salary: number;
  currency?: string;
  payment_frequency: PaymentFrequencyEnum;
  effective_from: string;
}) => client.post<EmployeeSalary>('/payroll/salaries', data);

export const getEmployeeSalary = (empId: string) =>
  client.get<EmployeeSalary>(`/payroll/salaries/employee/${empId}`);
export const getEmployeeSalaryHistory = (empId: string) =>
  client.get<EmployeeSalary[]>(`/payroll/salaries/employee/${empId}/history`);

// Admin — records
export const createPayrollRecord = (data: {
  employee_id: string;
  pay_period_start: string;
  pay_period_end: string;
  components?: Array<{ component_type: string; amount: number; description?: string }>;
}) => client.post<PayrollRecord>('/payroll/records', data);

export const getEmployeePayrollRecords = (
  empId: string,
  params?: Record<string, string | number>,
) => client.get<PayrollRecord[]>(`/payroll/records/employee/${empId}`, { params });

export const updatePayrollRecord = (
  id: string,
  data: Partial<Pick<PayrollRecord, 'payment_status' | 'payment_date' | 'payment_method' | 'payment_reference' | 'notes'>>,
) => client.patch<PayrollRecord>(`/payroll/records/${id}`, data);

export const processPayroll = (id: string) =>
  client.post<PayrollRecord>(`/payroll/records/${id}/process`);

export const getPayrollSummary = (params?: Record<string, string | number>) =>
  client.get('/payroll/summary', { params });
