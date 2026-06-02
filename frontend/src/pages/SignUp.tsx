import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

export default function SignUp() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await register(form);
      navigate(user.is_superuser ? '/admin' : '/employee');
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(
          Array.isArray(detail)
            ? (detail as Array<{ msg: string }>).map((d) => d.msg).join(', ')
            : (detail as string) ?? 'Sign up failed.',
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>HR Platform</h1>
        <h2>Create an account</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
            <div className="field">
              <label>Username (2–20 lowercase letters/numbers)</label>
              <input value={form.username} onChange={set('username')} autoFocus required />
            </div>
            <div className="field">
              <label>Email</label>
              <input type="email" value={form.email} onChange={set('email')} required />
            </div>
            <div className="field">
              <label>Password (min 8 chars)</label>
              <input type="password" value={form.password} onChange={set('password')} required />
            </div>
          </div>
          {error && <p className="msg-error">{error}</p>}
          <button type="submit" disabled={loading} style={{ width: '100%', marginTop: '0.75rem' }}>
            {loading ? 'Creating account…' : 'Sign Up'}
          </button>
        </form>
        <p>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
