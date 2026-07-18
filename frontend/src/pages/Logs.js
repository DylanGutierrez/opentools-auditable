import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';

export default function Logs() {
  const { t } = useTranslation();
  const { auditId } = useParams();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [toolFilter, setToolFilter] = useState('all');

  // Récupération des logs
  useEffect(() => {
    axios.get(`${API_URL}/logs/${auditId}`)
      .then((res) => setData(res.data))
      .catch((err) => {
        console.error(t('logLogsLoadError'), err);
        toast.error(err.response?.data?.error || t('toastLogsLoadError'));
      })
      .finally(() => setLoading(false));
  }, [auditId, t]);

  if (loading) return <p className="loader-text">{t('loading')}</p>;
  if (!data) return <div className="empty-state">{t('noLogData')}</div>;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('logsTitle')}</h2>
      <p className="page-subtitle">{t('logsSubtitle')}</p>

      <div className="form-group logs-filter">
        <label className="form-label">{t('filterByTool')}</label>
        <select value={toolFilter} onChange={(e) => setToolFilter(e.target.value)}>
          <option value="all">{t('allTools')}</option>
          <option value="nmap">Nmap</option>
          <option value="nikto">Nikto</option>
          <option value="wpscan">WPScan</option>
          <option value="nuclei">Nuclei</option>
          <option value="ndv">NDV/NVD</option>
          <option value="circl">CIRCL</option>
        </select>
      </div>

      <div className="target-list">
        {(data.targets || []).map((target) => {
          const logs = (target.logs || []).filter((item) => toolFilter === 'all' || item.tool === toolFilter);

          return (
            <div className="target-card" key={target.id}>
              <div className="target-header">
                <h3 className="target-title">{target.ip}</h3>
                <span className="audit-pill">{logs.length} {t('logsCount')}</span>
              </div>

              {logs.length === 0 ? (
                <div className="empty-state">{t('noLogsForTarget')}</div>
              ) : (
                logs.map((entry) => (
                  <div className="log-entry" key={`${entry.tool}-${entry.id}`}>
                    <div className="audit-vuln-head">
                      <span className="audit-pill">{entry.tool}</span>
                      <span className="audit-pill">{entry.horodatage || t('notAvailable')}</span>
                    </div>
                    {entry.request && <p className="target-meta"><strong>{t('request')} :</strong> {entry.request}</p>}
                    {entry.enumeration_option && <p className="target-meta"><strong>{t('enumeration')} :</strong> {entry.enumeration_option}</p>}
                    <pre className="log-content">{entry.log}</pre>
                  </div>
                ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}


