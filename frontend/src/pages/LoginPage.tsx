import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { login as apiLogin, getMe } from '../api/auth';
import { Activity, Lock, Mail, Loader2, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { setUser, isAuthenticated, setIsLoading, isLoading } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }
    setSubmitting(true);
    setErrorMsg('');
    try {
      const userObj = await apiLogin(email, password);
      setUser(userObj);
      navigate('/dashboard');
    } catch (err: any) {
      const errors = err.response?.data?.errors;
      if (errors && errors.length > 0) {
        setErrorMsg(errors[0].message);
      } else {
        setErrorMsg('Authentication failed. Check credentials and try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-fullpage">
        <Loader2 size={28} className="animate-spin" />
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Brand */}
        <div className="login-brand">
          <div className="login-brand-icon">
            <Activity size={24} />
          </div>
          <div>
            <h2>Breathe ESG Ingestor</h2>
            <p>Enterprise Carbon Data Normalization & Review</p>
          </div>
        </div>

        {/* Error */}
        {errorMsg && (
          <div className="login-error">
            <AlertCircle size={14} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label>Email Address</label>
            <div className="login-input-wrapper">
              <Mail size={15} />
              <input
                type="email"
                placeholder="analyst@demo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="login-field">
            <label>Password</label>
            <div className="login-input-wrapper">
              <Lock size={15} />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" disabled={submitting} className="btn btn-primary login-submit">
            {submitting ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                Signing in…
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>
            For demo credentials, run:<br />
            <code>python manage.py load_sample_data</code>
          </p>
        </div>
      </div>
    </div>
  );
};
