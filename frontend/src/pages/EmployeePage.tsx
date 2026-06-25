import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { getMyProfile, employeeSignUp, updateEmployee } from '../api/employee';
import { getMySalary, getMyPayroll } from '../api/payroll';
import { changePassword, updateMe } from '../api/auth';
import type { Employee, EmployeeSalary, PayrollRecord } from '../types';

type Tab = 'profile' | 'onboard' | 'payroll' | 'salary' | 'security';

const TABS: { id: Tab; label: string }[] = [
  { id: 'profile',  label: 'Profile'     },
  { id: 'onboard',  label: 'Onboarding'  },
  { id: 'payroll',  label: 'My Payroll'  },
  { id: 'salary',   label: 'My Salary'   },
  { id: 'security', label: 'Security'    },
];

export default function EmployeePage() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<Tab>('profile');
  const [profile, setProfile] = useState<Employee | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);

  useEffect(() => {
    getMyProfile()
      .then((res) => setProfile(res.data))
      .catch(() => {})
      .finally(() => setProfileLoading(false));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <h1>Employee Portal</h1>
        <div className="user-info">
          <span>{user!.username}</span>
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
        {tab === 'profile'  && <ProfileTab  profile={profile} loading={profileLoading} onUpdate={setProfile} />}
        {tab === 'onboard'  && <OnboardTab  profile={profile} onComplete={setProfile}  />}
        {tab === 'payroll'  && <PayrollTab  />}
        {tab === 'salary'   && <SalaryTab   />}
        {tab === 'security' && <SecurityTab />}
      </main>
    </div>
  );
}

/* ── Profile ──────────────────────────────────── */
function ProfileTab({
  profile,
  loading,
  onUpdate,
}: {
  profile: Employee | null;
  loading: boolean;
  onUpdate: (e: Employee) => void;
}) {
  const { user, setUser } = useAuth();
  const [empForm, setEmpForm] = useState({
    first_name: '', last_name: '', phone_number: '', gender: '', date_of_birth: '',
  });
  const [userForm, setUserForm] = useState({ username: user!.username, email: user!.email });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (profile) {
      setEmpForm({
        first_name:   profile.first_name      ?? '',
        last_name:    profile.last_name       ?? '',
        phone_number: profile.phone_number    ?? '',
        gender:       profile.gender          ?? '',
        date_of_birth: profile.date_of_birth  ?? '',
      });
    }
  }, [profile]);

  const saveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg('');
    try {
      const res = await updateMe(userForm);
      setUser(res.data);
      setMsg('Account updated.');
    } catch (err) {
      setMsg(axios.isAxiosError(err) ? (err.response?.data?.detail as string) : 'Update failed.');
    } finally { setSaving(false); }
  };

  const saveEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    setMsg('');
    try {
      const payload = Object.fromEntries(Object.entries(empForm).filter(([, v]) => v !== ''));
      const res = await updateEmployee(profile.id, payload);
      onUpdate(res.data);
      setMsg('Profile updated.');
    } catch (err) {
      setMsg(axios.isAxiosError(err) ? (err.response?.data?.detail as string) : 'Update failed.');
    } finally { setSaving(false); }
  };

  if (loading) return <p>Loading…</p>;

  return (
    <>
      <div className="section">
        <h2>Account</h2>
        <div className="info-grid">
          <div><strong>ID:</strong> {user!.id}</div>
          <div><strong>Username:</strong> {user!.username}</div>
          <div><strong>Email:</strong> {user!.email}</div>
          <div><strong>Role:</strong> {user!.is_superuser ? 'Admin' : 'Employee'}</div>
          {profile && <div><strong>Employee Code:</strong> {profile.employee_code}</div>}
          {profile && (
            <div>
              <strong>Status:</strong>{' '}
              <span className={`badge ${profile.employment_status}`}>{profile.employment_status}</span>
            </div>
          )}
        </div>
        <form onSubmit={saveUser}>
          <h3>Update Account</h3>
          <div className="form-grid">
            <div className="field">
              <label>Username</label>
              <input value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} />
            </div>
            <div className="field">
              <label>Email</label>
              <input type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} />
            </div>
          </div>
          {msg && <p className={msg.includes('updated') ? 'msg-ok' : 'msg-error'}>{msg}</p>}
          <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save Account'}</button>
        </form>
      </div>

      {profile ? (
        <div className="section">
          <form onSubmit={saveEmployee}>
            <h2>Employee Details</h2>
            <div className="form-grid">
              <div className="field">
                <label>First Name</label>
                <input value={empForm.first_name} onChange={(e) => setEmpForm({ ...empForm, first_name: e.target.value })} />
              </div>
              <div className="field">
                <label>Last Name</label>
                <input value={empForm.last_name} onChange={(e) => setEmpForm({ ...empForm, last_name: e.target.value })} />
              </div>
              <div className="field">
                <label>Phone</label>
                <input value={empForm.phone_number} onChange={(e) => setEmpForm({ ...empForm, phone_number: e.target.value })} />
              </div>
              <div className="field">
                <label>Gender</label>
                <select value={empForm.gender} onChange={(e) => setEmpForm({ ...empForm, gender: e.target.value })}>
                  <option value="">— select —</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
              <div className="field">
                <label>Date of Birth</label>
                <input type="date" value={empForm.date_of_birth} onChange={(e) => setEmpForm({ ...empForm, date_of_birth: e.target.value })} />
              </div>
            </div>
            <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save Employee Details'}</button>
          </form>
        </div>
      ) : (
        <div className="section">
          <p className="empty">No employee record yet — complete onboarding first.</p>
        </div>
      )}
    </>
  );
}

/* ── Onboard ──────────────────────────────────── */
function OnboardTab({
  profile,
  onComplete,
}: {
  profile: Employee | null;
  onComplete: (e: Employee) => void;
}) {
  const { user } = useAuth();
  const today = new Date().toISOString().split('T')[0];
  const [form, setForm] = useState({
    first_name: '', last_name: '',
    phone_number: '', date_of_birth: '', gender: '',
    employment_type: 'full_time', hire_date: today,
  });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  if (profile) {
    return (
      <div className="section">
        <h2>Onboarding</h2>
        <p className="msg-ok">
          You are onboarded as <strong>{profile.employee_code}</strong> - status:{' '}
          <span className={`badge ${profile.employment_status}`}>{profile.employment_status}</span>
        </p>
      </div>
    );
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg('');
    try {
      const payload = Object.fromEntries(
        Object.entries({ ...form, email: user!.email }).filter(([, v]) => v !== ''),
      ) as Parameters<typeof employeeSignUp>[0];
      const res = await employeeSignUp(payload);
      onComplete(res.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const d = err.response?.data?.detail;
        setMsg(Array.isArray(d) ? (d as Array<{ msg: string }>).map((x) => x.msg).join(', ') : (d as string) ?? 'Onboarding failed.');
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="section">
      <h2>Complete Onboarding</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="field"><label>First Name *</label><input value={form.first_name} onChange={set('first_name')} required /></div>
          <div className="field"><label>Last Name *</label><input value={form.last_name} onChange={set('last_name')} required /></div>
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
        </div>
        {msg && <p className="msg-error">{msg}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Submitting…' : 'Complete Onboarding'}</button>
      </form>
    </div>
  );
}

/* ── Payroll ──────────────────────────────────── */
function PayrollTab() {
  const [records, setRecords] = useState<PayrollRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyPayroll()
      .then((res) => setRecords(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="section">
      <h2>Payroll Records</h2>
      {loading ? (
        <p>Loading…</p>
      ) : records.length === 0 ? (
        <p className="empty">No payroll records yet.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Period</th><th>Gross</th><th>Deductions</th><th>Net</th><th>Status</th><th>Paid On</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td>{r.pay_period_start} – {r.pay_period_end}</td>
                  <td>{r.currency} {Number(r.gross_salary).toFixed(2)}</td>
                  <td>{r.currency} {Number(r.total_deductions).toFixed(2)}</td>
                  <td><strong>{r.currency} {Number(r.net_salary).toFixed(2)}</strong></td>
                  <td><span className={`badge ${r.payment_status}`}>{r.payment_status}</span></td>
                  <td>{r.payment_date ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ── Salary ───────────────────────────────────── */
function SalaryTab() {
  const [salary, setSalary] = useState<EmployeeSalary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMySalary()
      .then((res) => setSalary(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="section">
      <h2>Current Salary</h2>
      {loading ? (
        <p>Loading…</p>
      ) : !salary ? (
        <p className="empty">No salary information on record.</p>
      ) : (
        <div className="info-grid">
          <div><strong>Basic Salary:</strong> {salary.currency} {Number(salary.basic_salary).toFixed(2)}</div>
          <div><strong>Frequency:</strong> {salary.payment_frequency}</div>
          <div><strong>Effective From:</strong> {salary.effective_from}</div>
          {salary.effective_to && <div><strong>Effective To:</strong> {salary.effective_to}</div>}
          <div>
            <strong>Status:</strong>{' '}
            <span className={`badge ${salary.is_active ? 'active' : 'inactive'}`}>
              {salary.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Security ─────────────────────────────────── */
function SecurityTab() {
  const [form, setForm] = useState({ current_password: '', new_password: '' });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg('');
    try {
      await changePassword(form);
      setMsg('Password changed successfully.');
      setForm({ current_password: '', new_password: '' });
    } catch (err) {
      setMsg(axios.isAxiosError(err) ? (err.response?.data?.detail as string) : 'Failed to change password.');
    } finally { setLoading(false); }
  };

  return (
    <div className="section" style={{ maxWidth: 420 }}>
      <h2>Change Password</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
          <div className="field">
            <label>Current Password</label>
            <input type="password" value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} required />
          </div>
          <div className="field">
            <label>New Password</label>
            <input type="password" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} required />
          </div>
        </div>
        {msg && <p className={msg.includes('success') ? 'msg-ok' : 'msg-error'}>{msg}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Changing…' : 'Change Password'}</button>
      </form>
    </div>
  );
}
