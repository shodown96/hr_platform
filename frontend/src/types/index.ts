export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: Permission[];
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  description: string | null;
}

export type GenderEnum = 'male' | 'female' | 'other' | 'prefer_not_to_say';
export type EmploymentTypeEnum = 'full_time' | 'part_time' | 'contract' | 'intern';
export type EmploymentStatusEnum = 'active' | 'on_leave' | 'terminated' | 'suspended';
export type PaymentFrequencyEnum = 'weekly' | 'bi_weekly' | 'monthly' | 'annual';
export type PaymentStatusEnum = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Employee {
  id: string;
  user_id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  email: string;
  phone_number: string | null;
  date_of_birth: string | null;
  gender: GenderEnum | null;
  hire_date: string;
  termination_date: string | null;
  employment_type: EmploymentTypeEnum;
  employment_status: EmploymentStatusEnum;
  department_id: string | null;
  position_id: string | null;
  manager_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  parent_department_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Position {
  id: string;
  name: string;
  description: string | null;
  level: string | null;
  department_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeSalary {
  id: string;
  employee_id: string;
  basic_salary: number;
  currency: string;
  payment_frequency: PaymentFrequencyEnum;
  effective_from: string;
  effective_to: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayrollRecord {
  id: string;
  employee_id: string;
  employee_salary_id: string;
  pay_period_start: string;
  pay_period_end: string;
  gross_salary: number;
  total_deductions: number;
  net_salary: number;
  currency: string;
  payment_date: string | null;
  payment_method: string | null;
  payment_reference: string | null;
  payment_status: PaymentStatusEnum;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  user: User;
}
