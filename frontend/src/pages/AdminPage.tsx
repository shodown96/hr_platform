import { useState, useEffect, useCallback, type ReactNode, type FormEvent } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import {
  getUsers, createUser,
  getRoles, createRole, assignRole,
  getPermissions, createPermission, assignPermToRole, grantPermToUser,
  changePassword,
} from '../api/auth';
import {
  getEmployees, createEmployee, terminateEmployee,
  getDepartments, createDepartment,
  getPositions, createPosition,
} from '../api/employee';
import {
  createSalary, getEmployeeSalary,
  createPayrollRecord, getEmployeePayrollRecords, processPayroll,
} from '../api/payroll';
import type {
  User, Role, Permission, Employee, Department, Position,
  EmployeeSalary, PayrollRecord, PaymentFrequencyEnum,
} from '../types';

type AdminTab = 'users' | 'employees' | 'departments' | 'positions' | 'roles' | 'payroll' | 'security';

const TABS: { id: AdminTab; label: string }[] = [
  { id: 'users',       label: 'Users'               },
  { id: 'employees',   label: 'Employees'            },
  { id: 'departments', label: 'Departments'          },
  { id: 'positions',   label: 'Positions'            },
  { id: 'roles',       label: 'Roles & Permissions'  },
  { id: 'payroll',     label: 'Payroll'              },
  { id: 'security',    label: 'Security'             },
];

export default function AdminPage() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<AdminTab>('users');

  return (
    <div className="page">
      <header className="page-header">
        <h1>Admin Dashboard</h1>
        <div className="user-info">
          <span>{user!.username} (admin)</span>
          <button className="btn-secondary btn-sm" onClick={logout}>Logout</button>
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab${tab === t.id ? ' active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {tab === 'users'       && <UsersTab />}
        {tab === 'employees'   && <EmployeesTab />}
        {tab === 'departments' && <DepartmentsTab />}
        {tab === 'positions'   && <PositionsTab />}
        {tab === 'roles'       && <RolesTab />}
        {tab === 'payroll'     && <PayrollTab />}
        {tab === 'security'    && <SecurityTab />}
      </main>
    </div>
  );
}

/* ── Modal ────────────────────────────────────── */
function Modal({
  title, onClose, children,
}: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function errMsg(err: unknown): string {
  if (!axios.isAxiosError(err)) return 'An error occurred.';
  const d = err.response?.data?.detail;
  return Array.isArray(d) ? (d as Array<{ msg: string }>).map((x) => x.msg).join(', ') : (d as string) ?? 'Operation failed.';
}

/* ── Users ────────────────────────────────────── */
function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '', is_superuser: false });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    getUsers().then((r) => setUsers(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true); setMsg('');
    try {
      await createUser(form);
      setShow(false);
      setForm({ username: '', email: '', password: '', is_superuser: false });
      load();
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  return (
    <div className="section">
      <div className="section-header">
        <h2>Users ({users.length})</h2>
        <button className="btn-primary btn-sm" onClick={() => setShow(true)}>+ Create User</button>
      </div>
      {msg && <p className="msg-error">{msg}</p>}
      {loading ? <p>Loading…</p> : users.length === 0 ? <p className="empty">No users.</p> : (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Username</th><th>Email</th><th>Role</th><th>Active</th><th>Last Login</th><th>Joined</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td><strong>{u.username}</strong></td>
                  <td>{u.email}</td>
                  <td><span className={`badge ${u.is_superuser ? 'active' : 'inactive'}`}>{u.is_superuser ? 'Admin' : 'Employee'}</span></td>
                  <td><span className={`badge ${u.is_active ? 'active' : 'inactive'}`}>{u.is_active ? 'Yes' : 'No'}</span></td>
                  <td>{u.last_login ? new Date(u.last_login).toLocaleDateString() : '—'}</td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {show && (
        <Modal title="Create User" onClose={() => setShow(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="field"><label>Username</label><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></div>
              <div className="field"><label>Email</label><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
              <div className="field"><label>Password</label><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
              <div className="field">
                <label>Role</label>
                <select value={String(form.is_superuser)} onChange={(e) => setForm({ ...form, is_superuser: e.target.value === 'true' })}>
                  <option value="false">Employee</option>
                  <option value="true">Admin</option>
                </select>
              </div>
            </div>
            {msg && <p className="msg-error">{msg}</p>}
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShow(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

/* ── Employees ────────────────────────────────── */
function EmployeesTab() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [termTarget, setTermTarget] = useState<Employee | null>(null);
  const [msg, setMsg] = useState('');

  const today = new Date().toISOString().split('T')[0];
  const blankForm = {
    // Auth user fields (created first, not sent to employee service)
    username: '', password: '',
    // Employee fields
    first_name: '', last_name: '', email: '',
    phone_number: '', date_of_birth: '', gender: '',
    employment_type: 'full_time', hire_date: today,
    department_id: '', position_id: '',
  };
  const [form, setForm] = useState(blankForm);
  const [termForm, setTermForm] = useState({ reason: '', termination_date: '' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([getEmployees(), getDepartments(), getPositions()])
      .then(([e, d, p]) => { setEmployees(e.data); setDepartments(d.data); setPositions(p.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      // Step 1 — create the auth user
      const userRes = await createUser({
        username: form.username,
        email: form.email,
        password: form.password,
        is_superuser: false,
      });
      const userId = userRes.data.id;

      // Step 2 — create the employee record linked to that user
      const { username: _u, password: _p, ...employeeFields } = form;
      const merged = { ...employeeFields, user_id: userId };
      const payload = Object.fromEntries(
        Object.entries(merged).filter(([, v]) => v !== ''),
      ) as unknown as Parameters<typeof createEmployee>[0];
      await createEmployee(payload);

      setShowCreate(false);
      setForm(blankForm);
      load();
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  const handleTerminate = async (e: FormEvent) => {
    e.preventDefault(); if (!termTarget) return;
    setSaving(true);
    try {
      await terminateEmployee(termTarget.id, { employee_id: termTarget.id, reason: termForm.reason, termination_date: termForm.termination_date });
      setTermTarget(null); setTermForm({ reason: '', termination_date: '' }); load();
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="section">
      <div className="section-header">
        <h2>Employees ({employees.length})</h2>
        <button className="btn-primary btn-sm" onClick={() => setShowCreate(true)}>+ Add Employee</button>
      </div>
      {msg && <p className="msg-error">{msg}</p>}
      {loading ? <p>Loading…</p> : employees.length === 0 ? <p className="empty">No employees yet.</p> : (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Code</th><th>Name</th><th>Email</th><th>Type</th><th>Status</th><th>Hired</th><th></th></tr></thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id}>
                  <td>{emp.employee_code}</td>
                  <td>{emp.first_name} {emp.last_name}</td>
                  <td>{emp.email}</td>
                  <td>{emp.employment_type.replace('_', ' ')}</td>
                  <td><span className={`badge ${emp.employment_status}`}>{emp.employment_status}</span></td>
                  <td>{emp.hire_date}</td>
                  <td>
                    {emp.employment_status === 'active' && (
                      <button className="btn-danger btn-sm" onClick={() => { setTermTarget(emp); setMsg(''); }}>Terminate</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <Modal title="Add Employee" onClose={() => setShowCreate(false)}>
          <p style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.75rem' }}>
            Creates a login account and employee record in one step.
          </p>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="field"><label>Username *</label><input value={form.username} onChange={set('username')} required /></div>
              <div className="field"><label>Password *</label><input type="password" value={form.password} onChange={set('password')} required /></div>
              <div className="field"><label>First Name *</label><input value={form.first_name} onChange={set('first_name')} required /></div>
              <div className="field"><label>Last Name *</label><input value={form.last_name} onChange={set('last_name')} required /></div>
              <div className="field"><label>Email *</label><input type="email" value={form.email} onChange={set('email')} required /></div>
              <div className="field"><label>Phone</label><input value={form.phone_number} onChange={set('phone_number')} /></div>
              <div className="field"><label>Date of Birth</label><input type="date" value={form.date_of_birth} onChange={set('date_of_birth')} /></div>
              <div className="field">
                <label>Gender</label>
                <select value={form.gender} onChange={set('gender')}>
                  <option value="">— select —</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
              <div className="field">
                <label>Employment Type *</label>
                <select value={form.employment_type} onChange={set('employment_type')} required>
                  <option value="full_time">Full Time</option>
                  <option value="part_time">Part Time</option>
                  <option value="contract">Contract</option>
                  <option value="intern">Intern</option>
                </select>
              </div>
              <div className="field"><label>Hire Date *</label><input type="date" value={form.hire_date} onChange={set('hire_date')} required /></div>
              <div className="field">
                <label>Department</label>
                <select value={form.department_id} onChange={set('department_id')}>
                  <option value="">— none —</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Position</label>
                <select value={form.position_id} onChange={set('position_id')}>
                  <option value="">— none —</option>
                  {positions.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
            </div>
            {msg && <p className="msg-error">{msg}</p>}
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {termTarget && (
        <Modal title={`Terminate ${termTarget.first_name} ${termTarget.last_name}`} onClose={() => setTermTarget(null)}>
          <form onSubmit={handleTerminate}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field"><label>Reason *</label><input value={termForm.reason} onChange={(e) => setTermForm({ ...termForm, reason: e.target.value })} required /></div>
              <div className="field"><label>Termination Date *</label><input type="datetime-local" value={termForm.termination_date} onChange={(e) => setTermForm({ ...termForm, termination_date: e.target.value })} required /></div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setTermTarget(null)}>Cancel</button>
              <button type="submit" className="btn-danger" disabled={saving}>{saving ? 'Terminating…' : 'Terminate'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

/* ── Departments ──────────────────────────────── */
function DepartmentsTab() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    getDepartments().then((r) => setDepartments(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      await createDepartment(form);
      setShow(false); setForm({ name: '', description: '' }); load();
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  return (
    <div className="section">
      <div className="section-header">
        <h2>Departments ({departments.length})</h2>
        <button className="btn-primary btn-sm" onClick={() => setShow(true)}>+ Add Department</button>
      </div>
      {msg && <p className="msg-error">{msg}</p>}
      {loading ? <p>Loading…</p> : departments.length === 0 ? <p className="empty">No departments yet.</p> : (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Name</th><th>Description</th><th>Parent</th><th>Created</th></tr></thead>
            <tbody>
              {departments.map((d) => (
                <tr key={d.id}>
                  <td><strong>{d.name}</strong></td>
                  <td>{d.description ?? '—'}</td>
                  <td>{d.parent_department_id ?? '—'}</td>
                  <td>{new Date(d.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {show && (
        <Modal title="Add Department" onClose={() => setShow(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field"><label>Name *</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
              <div className="field"><label>Description</label><input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShow(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

/* ── Positions ────────────────────────────────── */
function PositionsTab() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', level: '', department_id: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([getPositions(), getDepartments()])
      .then(([p, d]) => { setPositions(p.data); setDepartments(d.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== '')) as Parameters<typeof createPosition>[0];
      await createPosition(payload);
      setShow(false); setForm({ name: '', description: '', level: '', department_id: '' }); load();
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  return (
    <div className="section">
      <div className="section-header">
        <h2>Positions ({positions.length})</h2>
        <button className="btn-primary btn-sm" onClick={() => setShow(true)}>+ Add Position</button>
      </div>
      {msg && <p className="msg-error">{msg}</p>}
      {loading ? <p>Loading…</p> : positions.length === 0 ? <p className="empty">No positions yet.</p> : (
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Name</th><th>Level</th><th>Description</th><th>Department</th></tr></thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.id}>
                  <td><strong>{p.name}</strong></td>
                  <td>{p.level ?? '—'}</td>
                  <td>{p.description ?? '—'}</td>
                  <td>{departments.find((d) => d.id === p.department_id)?.name ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {show && (
        <Modal title="Add Position" onClose={() => setShow(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field"><label>Name *</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
              <div className="field"><label>Level</label><input value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} placeholder="e.g. Senior" /></div>
              <div className="field"><label>Description</label><input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              <div className="field">
                <label>Department</label>
                <select value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
                  <option value="">— none —</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShow(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

/* ── Roles & Permissions ──────────────────────── */
function RolesTab() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);

  const [showCreateRole, setShowCreateRole] = useState(false);
  const [showCreatePerm, setShowCreatePerm] = useState(false);
  const [showAssignRole, setShowAssignRole] = useState(false);
  const [showAssignPermRole, setShowAssignPermRole] = useState<Role | null>(null);
  const [showAssignPermUser, setShowAssignPermUser] = useState(false);

  const [roleForm, setRoleForm] = useState({ name: '', description: '' });
  const [permForm, setPermForm] = useState({ resource: '', action: '', description: '' });
  const [assignRoleForm, setAssignRoleForm] = useState({ user_id: '', role_id: '' });
  const [assignPermRoleForm, setAssignPermRoleForm] = useState({ role_id: '', permission_id: '' });
  const [assignPermUserForm, setAssignPermUserForm] = useState({ user_id: '', permission_id: '' });

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([getRoles(), getPermissions(), getUsers()])
      .then(([r, p, u]) => { setRoles(r.data); setPermissions(p.data); setUsers(u.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const wrap = (fn: () => Promise<unknown>, onDone: () => void) => async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try { await fn(); onDone(); load(); }
    catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  return (
    <>
      <div className="section">
        <div className="section-header">
          <h2>Roles ({roles.length})</h2>
          <div className="actions">
            <button className="btn-primary btn-sm" onClick={() => setShowCreateRole(true)}>+ Create Role</button>
            <button className="btn-sm" style={{ background: '#6366f1', color: '#fff' }} onClick={() => setShowAssignRole(true)}>Assign Role to User</button>
          </div>
        </div>
        {msg && <p className="msg-error">{msg}</p>}
        {loading ? <p>Loading…</p> : roles.length === 0 ? <p className="empty">No roles yet.</p> : (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Description</th><th>Permissions</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {roles.map((r) => (
                  <tr key={r.id}>
                    <td><strong>{r.name}</strong></td>
                    <td>{r.description ?? '—'}</td>
                    <td>
                      {r.permissions && r.permissions.length > 0
                        ? <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                            {r.permissions.map((p) => (
                              <code key={p.id} style={{ fontSize: '0.72rem', background: '#eff6ff', color: '#1d4ed8', padding: '1px 5px', borderRadius: 4, border: '1px solid #bfdbfe' }}>
                                {p.resource}:{p.action}
                              </code>
                            ))}
                          </div>
                        : <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>No permissions</span>
                      }
                    </td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn-sm" style={{ background: '#0891b2', color: '#fff' }}
                        onClick={() => { setAssignPermRoleForm({ role_id: r.id, permission_id: '' }); setShowAssignPermRole(r); }}>
                        + Permission
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="section">
        <div className="section-header">
          <h2>Permissions ({permissions.length})</h2>
          <div className="actions">
            <button className="btn-primary btn-sm" onClick={() => setShowCreatePerm(true)}>+ Create Permission</button>
            <button className="btn-sm" style={{ background: '#6366f1', color: '#fff' }} onClick={() => setShowAssignPermUser(true)}>Grant to User</button>
          </div>
        </div>
        {loading ? <p>Loading…</p> : permissions.length === 0 ? <p className="empty">No permissions yet.</p> : (
          <div className="table-wrap">
            <table className="data-table">
              <thead><tr><th>Key</th><th>Resource</th><th>Action</th><th>Description</th></tr></thead>
              <tbody>
                {permissions.map((p) => (
                  <tr key={p.id}>
                    <td><code>{p.resource}:{p.action}</code></td>
                    <td>{p.resource}</td>
                    <td>{p.action}</td>
                    <td>{p.description ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showCreateRole && (
        <Modal title="Create Role" onClose={() => setShowCreateRole(false)}>
          <form onSubmit={wrap(() => createRole(roleForm), () => { setShowCreateRole(false); setRoleForm({ name: '', description: '' }); })}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field"><label>Name *</label><input value={roleForm.name} onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })} required /></div>
              <div className="field"><label>Description</label><input value={roleForm.description} onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })} /></div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowCreateRole(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showCreatePerm && (
        <Modal title="Create Permission" onClose={() => setShowCreatePerm(false)}>
          <form onSubmit={wrap(() => createPermission(permForm), () => { setShowCreatePerm(false); setPermForm({ resource: '', action: '', description: '' }); })}>
            <div className="form-grid">
              <div className="field"><label>Resource *</label><input value={permForm.resource} onChange={(e) => setPermForm({ ...permForm, resource: e.target.value })} placeholder="e.g. employee" required /></div>
              <div className="field"><label>Action *</label><input value={permForm.action} onChange={(e) => setPermForm({ ...permForm, action: e.target.value })} placeholder="e.g. read" required /></div>
              <div className="field" style={{ gridColumn: '1/-1' }}><label>Description</label><input value={permForm.description} onChange={(e) => setPermForm({ ...permForm, description: e.target.value })} /></div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowCreatePerm(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showAssignRole && (
        <Modal title="Assign Role to User" onClose={() => setShowAssignRole(false)}>
          <form onSubmit={wrap(() => assignRole(assignRoleForm), () => setShowAssignRole(false))}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field">
                <label>User *</label>
                <select value={assignRoleForm.user_id} onChange={(e) => setAssignRoleForm({ ...assignRoleForm, user_id: e.target.value })} required>
                  <option value="">— select —</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.username} ({u.email})</option>)}
                </select>
              </div>
              <div className="field">
                <label>Role *</label>
                <select value={assignRoleForm.role_id} onChange={(e) => setAssignRoleForm({ ...assignRoleForm, role_id: e.target.value })} required>
                  <option value="">— select —</option>
                  {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowAssignRole(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Assigning…' : 'Assign'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showAssignPermRole && (
        <Modal title={`Add Permission to "${showAssignPermRole.name}"`} onClose={() => setShowAssignPermRole(null)}>
          <form onSubmit={wrap(() => assignPermToRole(assignPermRoleForm), () => setShowAssignPermRole(null))}>
            <div className="field">
              <label>Permission *</label>
              <select value={assignPermRoleForm.permission_id} onChange={(e) => setAssignPermRoleForm({ ...assignPermRoleForm, permission_id: e.target.value })} required>
                <option value="">— select —</option>
                {permissions.map((p) => <option key={p.id} value={p.id}>{p.resource}:{p.action}</option>)}
              </select>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowAssignPermRole(null)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Assigning…' : 'Assign'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showAssignPermUser && (
        <Modal title="Grant Permission to User" onClose={() => setShowAssignPermUser(false)}>
          <form onSubmit={wrap(() => grantPermToUser(assignPermUserForm), () => setShowAssignPermUser(false))}>
            <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="field">
                <label>User *</label>
                <select value={assignPermUserForm.user_id} onChange={(e) => setAssignPermUserForm({ ...assignPermUserForm, user_id: e.target.value })} required>
                  <option value="">— select —</option>
                  {users.map((u) => <option key={u.id} value={u.id}>{u.username} ({u.email})</option>)}
                </select>
              </div>
              <div className="field">
                <label>Permission *</label>
                <select value={assignPermUserForm.permission_id} onChange={(e) => setAssignPermUserForm({ ...assignPermUserForm, permission_id: e.target.value })} required>
                  <option value="">— select —</option>
                  {permissions.map((p) => <option key={p.id} value={p.id}>{p.resource}:{p.action}</option>)}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowAssignPermUser(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Granting…' : 'Grant'}</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

/* ── Payroll ──────────────────────────────────── */
function PayrollTab() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Employee | null>(null);
  const [salary, setSalary] = useState<EmployeeSalary | null>(null);
  const [records, setRecords] = useState<PayrollRecord[]>([]);
  const [view, setView] = useState<'salary' | 'records'>('salary');
  const [msg, setMsg] = useState('');
  const [saving, setSaving] = useState(false);

  const [showSalaryModal, setShowSalaryModal] = useState(false);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const today = new Date().toISOString().split('T')[0];
  const [salaryForm, setSalaryForm] = useState<{ employee_id: string; basic_salary: string; currency: string; payment_frequency: PaymentFrequencyEnum; effective_from: string }>({
    employee_id: '', basic_salary: '', currency: 'USD', payment_frequency: 'monthly', effective_from: today,
  });
  const [recordForm, setRecordForm] = useState({ employee_id: '', pay_period_start: '', pay_period_end: '' });

  useEffect(() => {
    setLoading(true);
    getEmployees().then((r) => setEmployees(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const selectEmployee = async (emp: Employee) => {
    setSelected(emp); setMsg(''); setSalary(null); setRecords([]);
    setSalaryForm((f) => ({ ...f, employee_id: emp.id }));
    setRecordForm((f) => ({ ...f, employee_id: emp.id }));
    const [s, r] = await Promise.all([
      getEmployeeSalary(emp.id).catch(() => ({ data: null })),
      getEmployeePayrollRecords(emp.id).catch(() => ({ data: [] })),
    ]);
    setSalary(s.data as EmployeeSalary | null);
    setRecords(r.data as PayrollRecord[]);
  };

  const handleProcess = async (id: string) => {
    try { await processPayroll(id); if (selected) void selectEmployee(selected); }
    catch (err) { setMsg(errMsg(err)); }
  };

  const handleSalarySave = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      await createSalary({ ...salaryForm, basic_salary: parseFloat(salaryForm.basic_salary) });
      setShowSalaryModal(false);
      if (selected) void selectEmployee(selected);
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  const handleRecordCreate = async (e: FormEvent) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      await createPayrollRecord(recordForm);
      setShowRecordModal(false);
      setRecordForm({ employee_id: selected?.id ?? '', pay_period_start: '', pay_period_end: '' });
      if (selected) void selectEmployee(selected);
    } catch (err) { setMsg(errMsg(err)); }
    finally { setSaving(false); }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '1.25rem', alignItems: 'start' }}>
      <div className="section" style={{ maxHeight: 600, overflowY: 'auto' }}>
        <h2>Employees</h2>
        {loading ? <p>Loading…</p> : (
          <ul style={{ listStyle: 'none' }}>
            {employees.map((emp) => (
              <li key={emp.id} onClick={() => void selectEmployee(emp)} style={{
                padding: '0.55rem 0.5rem', cursor: 'pointer', borderRadius: 5,
                background: selected?.id === emp.id ? '#eff6ff' : 'transparent',
                borderLeft: selected?.id === emp.id ? '3px solid #2563eb' : '3px solid transparent',
                marginBottom: 2,
              }}>
                <div style={{ fontWeight: 500 }}>{emp.first_name} {emp.last_name}</div>
                <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{emp.employee_code}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        {!selected ? (
          <div className="section"><p className="empty">Select an employee to manage payroll.</p></div>
        ) : (
          <div className="section">
            <div className="section-header">
              <h2>{selected.first_name} {selected.last_name}</h2>
              <div className="actions">
                <button className={`btn-sm${view === 'salary' ? ' btn-primary' : ''}`} onClick={() => setView('salary')}>Salary</button>
                <button className={`btn-sm${view === 'records' ? ' btn-primary' : ''}`} onClick={() => setView('records')}>Records</button>
              </div>
            </div>
            {msg && <p className="msg-error">{msg}</p>}

            {view === 'salary' && (
              <>
                {salary ? (
                  <div className="info-grid">
                    <div><strong>Basic Salary:</strong> {salary.currency} {Number(salary.basic_salary).toFixed(2)}</div>
                    <div><strong>Frequency:</strong> {salary.payment_frequency}</div>
                    <div><strong>Effective From:</strong> {salary.effective_from}</div>
                    <div><strong>Status:</strong> <span className={`badge ${salary.is_active ? 'active' : 'inactive'}`}>{salary.is_active ? 'Active' : 'Inactive'}</span></div>
                  </div>
                ) : (
                  <p className="empty" style={{ marginBottom: '0.75rem' }}>No salary on record.</p>
                )}
                <button className="btn-primary btn-sm" onClick={() => setShowSalaryModal(true)}>
                  {salary ? 'Update Salary' : 'Set Salary'}
                </button>
              </>
            )}

            {view === 'records' && (
              <>
                <button className="btn-primary btn-sm" style={{ marginBottom: '0.75rem' }} onClick={() => setShowRecordModal(true)}>+ Create Record</button>
                {records.length === 0 ? <p className="empty">No records.</p> : (
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead><tr><th>Period</th><th>Gross</th><th>Net</th><th>Status</th><th></th></tr></thead>
                      <tbody>
                        {records.map((r) => (
                          <tr key={r.id}>
                            <td>{r.pay_period_start} – {r.pay_period_end}</td>
                            <td>{r.currency} {Number(r.gross_salary).toFixed(2)}</td>
                            <td>{r.currency} {Number(r.net_salary).toFixed(2)}</td>
                            <td><span className={`badge ${r.payment_status}`}>{r.payment_status}</span></td>
                            <td>
                              {r.payment_status === 'pending' && (
                                <button className="btn-success btn-sm" onClick={() => void handleProcess(r.id)}>Process</button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {showSalaryModal && (
        <Modal title="Set Salary" onClose={() => setShowSalaryModal(false)}>
          <form onSubmit={(e) => void handleSalarySave(e)}>
            <div className="form-grid">
              <div className="field"><label>Basic Salary *</label><input type="number" step="0.01" value={salaryForm.basic_salary} onChange={(e) => setSalaryForm({ ...salaryForm, basic_salary: e.target.value })} required /></div>
              <div className="field"><label>Currency</label><input value={salaryForm.currency} onChange={(e) => setSalaryForm({ ...salaryForm, currency: e.target.value })} maxLength={3} /></div>
              <div className="field">
                <label>Frequency *</label>
                <select value={salaryForm.payment_frequency} onChange={(e) => setSalaryForm({ ...salaryForm, payment_frequency: e.target.value as PaymentFrequencyEnum })}>
                  <option value="weekly">Weekly</option>
                  <option value="bi_weekly">Bi-Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="annual">Annual</option>
                </select>
              </div>
              <div className="field"><label>Effective From *</label><input type="date" value={salaryForm.effective_from} onChange={(e) => setSalaryForm({ ...salaryForm, effective_from: e.target.value })} required /></div>
            </div>
            {msg && <p className="msg-error">{msg}</p>}
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowSalaryModal(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {showRecordModal && (
        <Modal title="Create Payroll Record" onClose={() => setShowRecordModal(false)}>
          <form onSubmit={(e) => void handleRecordCreate(e)}>
            <div className="form-grid">
              <div className="field"><label>Period Start *</label><input type="date" value={recordForm.pay_period_start} onChange={(e) => setRecordForm({ ...recordForm, pay_period_start: e.target.value })} required /></div>
              <div className="field"><label>Period End *</label><input type="date" value={recordForm.pay_period_end} onChange={(e) => setRecordForm({ ...recordForm, pay_period_end: e.target.value })} required /></div>
            </div>
            {msg && <p className="msg-error">{msg}</p>}
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowRecordModal(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

/* ── Security ─────────────────────────────────── */
function SecurityTab() {
  const [form, setForm] = useState({ current_password: '', new_password: '' });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault(); setLoading(true); setMsg('');
    try {
      await changePassword(form);
      setMsg('Password changed successfully.');
      setForm({ current_password: '', new_password: '' });
    } catch (err) { setMsg(errMsg(err)); }
    finally { setLoading(false); }
  };

  return (
    <div className="section" style={{ maxWidth: 420 }}>
      <h2>Change Password</h2>
      <form onSubmit={(e) => void handleSubmit(e)}>
        <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
          <div className="field"><label>Current Password</label><input type="password" value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} required /></div>
          <div className="field"><label>New Password</label><input type="password" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} required /></div>
        </div>
        {msg && <p className={msg.includes('success') ? 'msg-ok' : 'msg-error'}>{msg}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Changing…' : 'Change Password'}</button>
      </form>
    </div>
  );
}
