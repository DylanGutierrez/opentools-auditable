import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';

export default function Analyses() {
  const { t } = useTranslation();
  const { auditId } = useParams();

  const [isSigned, setIsSigned] = useState(false);
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);

  const [currentId, setCurrentId] = useState(null);
  const [ip, setIp] = useState('');
  const [ports, setPorts] = useState('');

  // Choix des outils de scan
  const [tools, setTools] = useState(() => {
    try {
      const savedTools = localStorage.getItem(`audit-tools-${auditId}`);
      return savedTools ? JSON.parse(savedTools) : { nmap: true, wpscan: false, nikto: false, nuclei: false };
    } catch {
      return { nmap: true, wpscan: false, nikto: false, nuclei: false };
    }
  });

  // Récupération du périmètre IP / Ports
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

  const handleToolChange = (tool, checked) => {
    const nextTools = { ...tools, [tool]: checked };
    setTools(nextTools);
    localStorage.setItem(`audit-tools-${auditId}`, JSON.stringify(nextTools));
  };

  const resetForm = () => {
    setCurrentId(null);
    setIp('');
    setPorts('');
  };

  // Limitation de la saisie des IP / Port pour éviter les erreurs
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

  // Lancement de l'analyse
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
            onChange={(e) => handleToolChange('nmap', e.target.checked)}
          /> {t('toolNmap')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.wpscan}
            disabled={isSigned}
            onChange={(e) => handleToolChange('wpscan', e.target.checked)}
          /> {t('toolWPScan')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.nikto}
            disabled={isSigned}
            onChange={(e) => handleToolChange('nikto', e.target.checked)}
          /> {t('toolNikto')}
        </label>

        <label className="checkbox-item">
          <input
            type="checkbox"
            checked={tools.nuclei}
            disabled={isSigned}
            onChange={(e) => handleToolChange('nuclei', e.target.checked)}
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

