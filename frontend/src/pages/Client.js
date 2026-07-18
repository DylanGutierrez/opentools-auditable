import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';

export default function Client() {
  const { t } = useTranslation();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasAuditResults, setHasAuditResults] = useState(false);
  const navigate = useNavigate();

  // Récupération du client et de l'état de l'audit
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

            <button
              className="btn-secondary"
              onClick={() => navigate(`/client/${client.audit_id}/settings`)}
            >
              {t('settings')}
            </button>

            <button
              className="btn-secondary"
              onClick={() => navigate(`/client/${client.audit_id}/logs`)}
            >
              {t('logs')}
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

