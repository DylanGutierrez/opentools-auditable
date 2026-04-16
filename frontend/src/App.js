import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

const API_URL = "http://localhost:5000/api";

function App() {
  const [username, setUsername] = useState("");
  const { t, i18n } = useTranslation();

  useEffect(() => {
    axios.get(`${API_URL}/config`)
      .then((res) => setUsername(res.data.username || ""))
      .catch((err) => {
        console.error(t('logConfigLoadError'), err);
        toast.error(t('toastConfigLoadError'));
      });
  }, [t]);

  return (
    <Router>
      <div className="app-shell">
        <nav className="topbar">
          <div className="topbar-inner">
            <div className="brand-block">
              <h2>{t('appTitle')}</h2>
              <div className="brand-subtitle">
                {t('connectedAs', { username: username || t('unknownUser') })}
              </div>
            </div>

            <div className="nav-links">
              <Link to="/" className="nav-link">{t('home')}</Link>
              <Link to="/client" className="nav-link">{t('client')}</Link>

              <select
                className="language-select"
                value={i18n.language}
                onChange={(e) => i18n.changeLanguage(e.target.value)}
                aria-label={t('language')}
              >
                <option value="fr">{t('languageFrench')}</option>
                <option value="en">{t('languageEnglish')}</option>
              </select>
            </div>
          </div>
        </nav>

        <div className="page-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="/client" element={<Client />} />
            <Route path="/client/add" element={<AddClient />} />
            <Route path="/client/edit" element={<EditClient />} />
            <Route path="/client/:auditId/convention" element={<Convention />} />
            <Route path="/client/:auditId/analyses" element={<Analyses />} />
            <Route path="/client/:auditId/audit" element={<AuditReport />} />
          </Routes>
        </div>

        <ToastContainer />
      </div>
    </Router>
  );
}

function Home() {
  const { t } = useTranslation();

  return (
    <div className="page-card">
      <h1 className="page-title">{t('welcomeTitle')}</h1>
      <p className="page-subtitle">{t('welcomeSubtitle')}</p>
    </div>
  );
}

function Client() {
  const { t } = useTranslation();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasAuditResults, setHasAuditResults] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/client`)
      .then((res) => {
        const clientData = res.data || null;
        setClient(clientData);

        if (clientData?.audit_id) {
          return axios.get(`${API_URL}/audit/${clientData.audit_id}/report`)
            .then((auditRes) => {
              setHasAuditResults(!!auditRes.data?.has_results);
            })
            .catch((err) => {
              console.error(t('logAuditLoadError'), err);
              setHasAuditResults(false);
            });
        }

        setHasAuditResults(false);
      })
      .catch((err) => {
        console.error(t('logClientLoadError'), err);
        toast.error(err.response?.data?.error || t('toastClientLoadError'));
      })
      .finally(() => setLoading(false));
  }, [t]);

  if (loading) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card">
      <h1 className="page-title">{t('clientDetails')}</h1>

      {client ? (
        <>
          <div className="info-grid">
            <div className="info-item"><span className="info-label">{t('clientId')}</span><span className="info-value">{client.id}</span></div>
            <div className="info-item"><span className="info-label">{t('auditId')}</span><span className="info-value">{client.audit_id}</span></div>
            <div className="info-item"><span className="info-label">{t('company')}</span><span className="info-value">{client.company_name}</span></div>
            <div className="info-item"><span className="info-label">{t('manager')}</span><span className="info-value">{client.dirigeant}</span></div>
            <div className="info-item"><span className="info-label">{t('address')}</span><span className="info-value">{client.adresse}</span></div>
            <div className="info-item"><span className="info-label">{t('postalCode')}</span><span className="info-value">{client.postal_code}</span></div>
            <div className="info-item"><span className="info-label">{t('email')}</span><span className="info-value">{client.contact_mail}</span></div>
            <div className="info-item"><span className="info-label">{t('phone')}</span><span className="info-value">{client.contact_phone}</span></div>
          </div>

          <div className={`status-badge ${client.convention_signed ? 'signed' : 'unsigned'}`}>
            {client.convention_signed ? t('conventionSignedBadge') : t('conventionUnsignedBadge')}
          </div>

          <div className="actions-row">
            {!client.convention_signed && (
              <button className="btn-primary" onClick={() => navigate('/client/edit')}>
                {t('editClient')}
              </button>
            )}

            <button
              className="btn-secondary"
              onClick={() => navigate(`/client/${client.audit_id}/convention`)}
            >
              {t('viewConvention')}
            </button>

            <button
              className="btn-primary"
              onClick={() => navigate(`/client/${client.audit_id}/analyses`)}
            >
              {t('manageAnalyses')}
            </button>

            {hasAuditResults && (
              <button
                className="btn-success"
                onClick={() => navigate(`/client/${client.audit_id}/audit`)}
              >
                {t('viewAudit')}
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <p>{t('noClient')}</p>
          <div className="actions-row" style={{ justifyContent: 'center' }}>
            <button className="btn-primary" onClick={() => navigate('/client/add')}>
              {t('addClient')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ClientForm({ initialData, submitLabel, onSubmit }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState(initialData);

  useEffect(() => {
    setFormData(initialData);
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const submit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={submit} className="form-card">
      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">{t('companyNameLabel')}</label>
          <input
            type="text"
            name="company_name"
            placeholder={t('companyNamePlaceholder')}
            value={formData.company_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('managerLabel')}</label>
          <input
            type="text"
            name="dirigeant"
            placeholder={t('managerPlaceholder')}
            value={formData.dirigeant}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group full-width">
          <label className="form-label">{t('addressLabel')}</label>
          <input
            type="text"
            name="adresse"
            placeholder={t('addressPlaceholder')}
            value={formData.adresse}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('postalCodeLabel')}</label>
          <input
            type="text"
            name="postal_code"
            placeholder={t('postalCodePlaceholder')}
            value={formData.postal_code}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('phoneLabel')}</label>
          <input
            type="text"
            name="contact_phone"
            placeholder={t('phonePlaceholder')}
            value={formData.contact_phone}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group full-width">
          <label className="form-label">{t('emailLabel')}</label>
          <input
            type="email"
            name="contact_mail"
            placeholder={t('emailPlaceholder')}
            value={formData.contact_mail}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="actions-row">
        <button className="btn-primary" type="submit">{submitLabel}</button>
      </div>
    </form>
  );
}

function AddClient() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/client`)
      .then((res) => {
        if (res.data) {
          toast.error(t('toastClientAlreadyExists'));
          navigate('/client');
        }
      })
      .catch((err) => {
        console.error(t('logClientCheckError'), err);
      });
  }, [navigate, t]);

  const handleSubmit = (formData) => {
    axios.post(`${API_URL}/client`, formData)
      .then(() => {
        toast.success(t('toastClientAdded'));
        navigate('/client');
      })
      .catch((err) => {
        console.error(t('logClientAddError'), err);
        toast.error(err.response?.data?.error || t('toastClientAddError'));
      });
  };

  return (
    <div className="page-card">
      <h2 className="page-title">{t('addClientTitle')}</h2>
      <ClientForm
        initialData={{
          company_name: '',
          dirigeant: '',
          adresse: '',
          postal_code: '',
          contact_mail: '',
          contact_phone: ''
        }}
        submitLabel={t('save')}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

function EditClient() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [client, setClient] = useState(null);

  useEffect(() => {
    axios.get(`${API_URL}/client`)
      .then((res) => {
        if (!res.data) {
          toast.error(t('toastNoClientToEdit'));
          navigate('/client');
          return;
        }
        if (res.data.convention_signed) {
          toast.error(t('toastClientLocked'));
          navigate('/client');
          return;
        }
        setClient(res.data);
      })
      .catch((err) => {
        console.error(t('logClientLoadError'), err);
        toast.error(err.response?.data?.error || t('toastClientLoadError'));
      });
  }, [navigate, t]);

  const handleSubmit = (formData) => {
    axios.put(`${API_URL}/client`, formData)
      .then((res) => {
        toast.success(res.data.message || t('toastClientUpdated'));
        navigate('/client');
      })
      .catch((err) => {
        console.error(t('logClientUpdateError'), err);
        toast.error(err.response?.data?.error || t('toastClientUpdateError'));
      });
  };

  if (!client) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('editClientTitle')}</h2>
      <ClientForm
        initialData={client}
        submitLabel={t('update')}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

function Convention() {
  const { t } = useTranslation();
  const { auditId } = useParams();
  const [isSigned, setIsSigned] = useState(false);
  const [targetCount, setTargetCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get(`${API_URL}/convention/${auditId}/status`),
      axios.get(`${API_URL}/scope/${auditId}`)
    ])
      .then(([statusRes, scopeRes]) => {
        setIsSigned(!!statusRes.data.signed);
        setTargetCount((scopeRes.data.targets || []).length);
      })
      .catch((err) => {
        console.error(t('logConventionLoadError'), err);
        toast.error(err.response?.data?.error || t('toastConventionLoadError'));
      })
      .finally(() => setLoading(false));
  }, [auditId, t]);

  const signConvention = () => {
    axios.post(`${API_URL}/convention/${auditId}/sign`)
      .then((res) => {
        toast.success(res.data.message || t('toastConventionSignedSuccess'));
        setIsSigned(true);
      })
      .catch((err) => {
        console.error(t('logConventionSignError'), err);
        toast.error(err.response?.data?.error || t('toastConventionSignError'));
      });
  };

  if (loading) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('conventionTitle')}</h2>
      <p className="page-subtitle">{t('conventionText')}</p>

      {isSigned ? (
        <div className="status-badge signed">{t('conventionAlreadySigned')}</div>
      ) : (
        <div className="actions-row">
          <button
            className="btn-success"
            onClick={signConvention}
            disabled={targetCount === 0}
            title={targetCount === 0 ? t('signConventionNeedTarget') : ''}
          >
            {t('signConvention')}
          </button>
        </div>
      )}

      {!isSigned && targetCount === 0 && (
        <p className="muted-text">{t('signConventionNeedTarget')}</p>
      )}
    </div>
  );
}

function Analyses() {
  const { t } = useTranslation();
  const { auditId } = useParams();

  const [isSigned, setIsSigned] = useState(false);
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);

  const [currentId, setCurrentId] = useState(null);
  const [ip, setIp] = useState('');
  const [ports, setPorts] = useState('');

  const [tools, setTools] = useState({
    nmap: true,
    wpscan: false,
    nikto: false,
    nuclei: false
  });

  const loadScope = () => {
    axios.get(`${API_URL}/scope/${auditId}`)
      .then((res) => {
        setIsSigned(!!res.data.signed);
        setTargets(res.data.targets || []);
      })
      .catch((err) => {
        console.error(t('logScopeLoadError'), err);
        toast.error(err.response?.data?.error || t('toastScopeLoadError'));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadScope();
  }, [auditId, t]);

  const resetForm = () => {
    setCurrentId(null);
    setIp('');
    setPorts('');
  };

  const handleValidate = () => {
    if (!ip.trim()) {
      toast.warning(t('toastIpRequired'));
      return;
    }

    axios.post(`${API_URL}/scope/${auditId}`, { ip, ports })
      .then((res) => {
        toast.success(res.data.message || t('toastTargetAdded'));
        resetForm();
        loadScope();
      })
      .catch((err) => {
        console.error(t('logTargetAddError'), err);
        toast.error(err.response?.data?.error || t('toastTargetAddedError'));
      });
  };

  const handleEdit = (target) => {
    setCurrentId(target.id);
    setIp(target.ip);
    setPorts(target.true_cmd_port || (target.ports || []).map((p) => p.port_number).join(","));
  };

  const handleUpdate = () => {
    if (!currentId) {
      toast.warning(t('toastNoTargetSelected'));
      return;
    }

    axios.put(`${API_URL}/scope/${auditId}/${currentId}`, { ip, ports })
      .then((res) => {
        toast.success(res.data.message || t('toastTargetUpdated'));
        resetForm();
        loadScope();
      })
      .catch((err) => {
        console.error(t('logTargetUpdateError'), err);
        toast.error(err.response?.data?.error || t('toastTargetUpdatedError'));
      });
  };

  const handleDelete = (id) => {
    axios.delete(`${API_URL}/scope/${auditId}/${id}`)
      .then((res) => {
        toast.success(res.data.message || t('toastTargetDeleted'));
        if (currentId === id) resetForm();
        loadScope();
      })
      .catch((err) => {
        console.error(t('logTargetDeleteError'), err);
        toast.error(err.response?.data?.error || t('toastTargetDeletedError'));
      });
  };

  const handleScan = () => {
    const selectedTools = Object.keys(tools).filter((tool) => tools[tool]);

    if (selectedTools.length === 0) {
      toast.warning(t('toastSelectAtLeastOneTool'));
      return;
    }

    if (!isSigned) {
      toast.error(t('toastConventionRequiredToScan'));
      return;
    }

    axios.post(`${API_URL}/scan/launch`, {
      audit_id: auditId,
      tools: selectedTools
    })
      .then((res) => toast.success(res.data.message || t('toastScanStarted')))
      .catch((err) => {
        console.error(t('logScanLaunchError'), err);
        toast.error(err.response?.data?.error || t('toastScanLaunchError'));
      });
  };

  if (loading) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('analysesTitle')}</h2>

      <div className={`status-badge ${isSigned ? 'signed' : 'unsigned'}`}>
        {isSigned ? t('conventionSignedBadge') : t('conventionUnsignedBadge')}
      </div>

      <h3 className="section-title">{t('scanTools')}</h3>
      <div className="checkbox-row">
        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.nmap}
            disabled={isSigned}
            onChange={(e) => setTools({ ...tools, nmap: e.target.checked })}
          /> {t('toolNmap')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.wpscan}
            disabled={isSigned}
            onChange={(e) => setTools({ ...tools, wpscan: e.target.checked })}
          /> {t('toolWPScan')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.nikto}
            disabled={isSigned}
            onChange={(e) => setTools({ ...tools, nikto: e.target.checked })}
          /> {t('toolNikto')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.nuclei}
            disabled={isSigned}
            onChange={(e) => setTools({ ...tools, nuclei: e.target.checked })}
          /> {t('toolNuclei')}
        </label>
      </div>

      <h3 className="section-title">{t('scopeTitle')}</h3>

      <div className="inline-form">
        <input
          type="text"
          placeholder={t('targetIpPlaceholder')}
          value={ip}
          onChange={(e) => setIp(e.target.value)}
          disabled={isSigned}
        />
        <input
          type="text"
          placeholder={t('targetPortsPlaceholder')}
          value={ports}
          onChange={(e) => setPorts(e.target.value)}
          disabled={isSigned}
        />
        <button className="btn-primary" onClick={handleValidate} disabled={isSigned}>
          {t('validate')}
        </button>
        <button className="btn-warning" onClick={handleUpdate} disabled={isSigned || !currentId}>
          {t('edit')}
        </button>
        <button className="btn-secondary" onClick={resetForm} disabled={isSigned}>
          {t('cancel')}
        </button>
      </div>

      <div className="target-list">
        {targets.length === 0 ? (
          <div className="empty-state">{t('noValidatedTarget')}</div>
        ) : (
          targets.map((target) => (
            <div key={target.id} className="target-card">
              <div className="target-header">
                <h4 className="target-title">{target.ip}</h4>
                <div className="actions-row">
                  <button className="btn-primary" onClick={() => handleEdit(target)} disabled={isSigned}>
                    {t('load')}
                  </button>
                  <button className="btn-danger" onClick={() => handleDelete(target.id)} disabled={isSigned}>
                    {t('delete')}
                  </button>
                </div>
              </div>

              <p className="target-meta">
                <strong>{t('ports')} :</strong>{" "}
                {target.port_count > 20
                  ? (target.true_cmd_port || t('none'))
                  : (target.ports && target.ports.length > 0
                      ? target.ports.map((p) => p.port_number).join(", ")
                      : t('none'))}
              </p>
            </div>
          ))
        )}
      </div>

      <div className="actions-row">
        <button
          className="btn-danger"
          onClick={handleScan}
          disabled={!isSigned}
        >
          {t('launchAnalysis')}
        </button>
      </div>
    </div>
  );
}

function AuditReport() {
  const { t } = useTranslation();
  const { auditId } = useParams();
  const [loading, setLoading] = useState(true);
  const [auditData, setAuditData] = useState(null);

  useEffect(() => {
    axios.get(`${API_URL}/audit/${auditId}/report`)
      .then((res) => {
        setAuditData(res.data);
      })
      .catch((err) => {
        console.error(t('logAuditLoadError'), err);
        toast.error(err.response?.data?.error || t('toastAuditLoadError'));
      })
      .finally(() => setLoading(false));
  }, [auditId, t]);

  if (loading) return <p className="loader-text">{t('loading')}</p>;
  if (!auditData) return <div className="empty-state">{t('noAuditData')}</div>;

  const { audit, vulnerabilities } = auditData;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('auditTitle')}</h2>

      <div className="info-grid">
        <div className="info-item"><span className="info-label">{t('client')}</span><span className="info-value">{audit.company_name}</span></div>
        <div className="info-item"><span className="info-label">{t('manager')}</span><span className="info-value">{audit.dirigeant}</span></div>
        <div className="info-item"><span className="info-label">{t('audit')}</span><span className="info-value">{audit.title}</span></div>
        <div className="info-item"><span className="info-label">{t('convention')}</span><span className="info-value">{audit.convention_signed ? t('signed') : t('unsigned')}</span></div>
      </div>

      {!vulnerabilities || vulnerabilities.length === 0 ? (
        <div className="empty-state">{t('noVulnerability')}</div>
      ) : (
        vulnerabilities.map((vuln) => (
          <div key={vuln.id} className="audit-vuln-card">
            <div className="audit-vuln-head">
              <div className="audit-pill">{t('cve')} : {vuln.CVE || t('notAvailable')}</div>
              <div className="audit-pill">{t('cvss')} : {vuln.CVSS || t('notAvailable')}</div>
            </div>

            <div className="table-wrapper">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>{t('cve')}</th>
                    <th>{t('criticality')}</th>
                    <th>{t('description')}</th>
                    <th>{t('remediation')}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{vuln.CVE || t('notAvailable')}</td>
                    <td>{vuln.criticity ?? t('notAvailable')}</td>
                    <td>{vuln.description || t('noDescription')}</td>
                    <td>{vuln.remediation || t('noRemediation')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default App;
