import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';
import {
  DEFAULT_AUDIT_TOOLS,
  TOOL_TRANSLATION_KEYS,
  readSelectedAuditTools,
  buildConventionPrintStyles
} from '../utils/convention';

export default function Convention() {
  const { t, i18n } = useTranslation();
  const { auditId } = useParams();
  const [isSigned, setIsSigned] = useState(false);
  const [targets, setTargets] = useState([]);
  const [client, setClient] = useState(null);
  const [settings, setSettings] = useState(null);
  const [auditInfo, setAuditInfo] = useState(null);
  const [config, setConfig] = useState(null);
  const [selectedTools, setSelectedTools] = useState(DEFAULT_AUDIT_TOOLS);
  const [loading, setLoading] = useState(true);

  // Récupération du périmètre, du client et des paramètres.
  useEffect(() => {
    setLoading(true);

    Promise.all([
      axios.get(`${API_URL}/convention/${auditId}/status`),
      axios.get(`${API_URL}/scope/${auditId}`),
      axios.get(`${API_URL}/settings/${auditId}`),
      axios.get(`${API_URL}/client`),
      axios.get(`${API_URL}/config`),
      axios.get(`${API_URL}/audit/${auditId}/report`).catch(() => ({ data: null }))
    ])
      .then(([statusRes, scopeRes, settingsRes, clientRes, configRes, auditRes]) => {
        setIsSigned(!!statusRes.data.signed);
        setTargets(scopeRes.data.targets || []);
        setSettings(settingsRes.data.settings || null);
        setClient(clientRes.data || null);
        setConfig(configRes.data || null);
        setAuditInfo(auditRes.data?.audit || null);
        setSelectedTools(readSelectedAuditTools(auditId));
      })
      .catch((err) => {
        console.error(t('logConventionLoadError'), err);
        toast.error(err.response?.data?.error || t('toastConventionLoadError'));
      })
      .finally(() => setLoading(false));
  }, [auditId, t]);

  const formatValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return t('notAvailable');
    }
    return String(value);
  };

  const formatOutput = (value) => value || t('noExport');

  const getToolParams = (tool) => {
    const setting = settings?.[tool] || {};

    if (tool === 'nmap') {
      return [
        `${t('aggressiveness')} : ${formatValue(setting.aggressiveness ?? 0)}`,
        `${t('outputFormat')} : ${formatOutput(setting.output_file)}`
      ];
    }

    if (tool === 'nikto') {
      return [
        `${t('aggressiveness')} : ${formatValue(setting.aggressiveness ?? 0)}`,
        `${t('outputFormat')} : ${formatOutput(setting.output_file)}`,
        `${t('niktoTuning')} : ${setting.tuning_option || t('none')}`
      ];
    }

    if (tool === 'wpscan') {
      return [
        `${t('aggressiveness')} : ${setting.aggressiveness ? t('enabled') : t('disabled')}`,
        `${t('outputFormat')} : ${formatOutput(setting.output_file)}`,
        `${t('wpscanEnumeration')} : ${setting.enumeration_mode || t('notAvailable')}`,
        `${t('wpscanEnumerationOption')} : ${setting.enumeration_option || t('notAvailable')}`
      ];
    }

    if (tool === 'nuclei') {
      return [
        `${t('aggressiveness')} : ${formatValue(setting.aggressiveness ?? 0)}`,
        `${t('outputFormat')} : ${formatOutput(setting.output_file)}`,
        `${t('nucleiSeverity')} : ${setting.severity || t('notAvailable')}`
      ];
    }

    return [];
  };

  const selectedToolKeys = Object.keys(selectedTools).filter((tool) => selectedTools[tool]);
  const targetCount = targets.length;
  const generatedDate = new Date().toLocaleDateString(i18n.language || 'fr', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const auditorName = config?.username || t('unknownUser');

  const conventionParagraphs = t('conventionGenericParagraphs', {
    returnObjects: true,
    auditorName,
    clientCompany: client?.company_name || t('notAvailable'),
    clientManager: client?.dirigeant || t('notAvailable'),
    clientAddress: [client?.adresse, client?.postal_code].filter(Boolean).join(' ') || t('notAvailable'),
    clientPostalCode: client?.postal_code || t('notAvailable'),
    clientEmail: client?.contact_mail || t('notAvailable'),
    clientPhone: client?.contact_phone || t('notAvailable'),
    auditId,
    auditTitle: auditInfo?.title || t('notAvailable'),
    auditStartDate: auditInfo?.started_at || t('notAvailable'),
    auditEndDate: auditInfo?.finished_at || t('notAvailable')
  });

  // Convention signée ou non ?
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

  // Export PDF de la convention
  const exportPdf = () => {
    const source = document.getElementById(`convention-document-${auditId}`);

    if (!source) {
      toast.error(t('toastPdfExportError'));
      return;
    }

    const html = `<!doctype html>
<html lang="${i18n.language || 'fr'}">
<head>
  <meta charset="utf-8" />
  <title>${t('conventionPdfTitle', { auditId })}</title>
  <style>${buildConventionPrintStyles()}</style>
</head>
<body>
  ${source.outerHTML}
  <script>
    window.addEventListener('load', function () {
      setTimeout(function () {
        window.focus();
        window.print();
      }, 350);
    });
  </script>
</body>
</html>`;

    // Ne pas utiliser noopener/noreferrer ici : certains navigateurs retournent null
    // même si un onglet about:blank est ouvert, ce qui laisse une page vide.
    const printWindow = window.open('', '_blank');

    if (!printWindow) {
      try {
        const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        toast.info(t('toastPdfFallbackOpened'));
      } catch (e) {
        console.error(e);
        toast.error(t('toastPdfPopupBlocked'));
      }
      return;
    }

    printWindow.document.open();
    printWindow.document.write(html);
    printWindow.document.close();
  };

  if (loading) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card convention-page-card">
      <div className="convention-document" id={`convention-document-${auditId}`}>
        <header className="convention-doc-header">
          <h2 className="convention-doc-title">{t('conventionTitle')}</h2>
          <p className="page-subtitle">{t('conventionSubtitle')}</p>
          <div className="convention-doc-meta">
            <span>{t('auditId')} : {auditId}</span>
            <span>{t('conventionGeneratedOn', { date: generatedDate })}</span>
            {auditInfo?.title && <span>{t('audit')} : {auditInfo.title}</span>}
          </div>
        </header>

        <section className="convention-section">
          <h3>{t('conventionPartiesTitle')}</h3>
          <div className="convention-party-grid">
            <div className="convention-party-card">
              <h4>{t('conventionAuditorTitle')}</h4>
              <p className="convention-field"><strong>{t('name')} :</strong> {formatValue(auditorName)}</p>
            </div>

            <div className="convention-party-card">
              <h4>{t('conventionClientTitle')}</h4>
              <p className="convention-field"><strong>{t('company')} :</strong> {formatValue(client?.company_name)}</p>
              <p className="convention-field"><strong>{t('manager')} :</strong> {formatValue(client?.dirigeant)}</p>
              <p className="convention-field"><strong>{t('address')} :</strong> {formatValue(client?.adresse)}</p>
              <p className="convention-field"><strong>{t('postalCode')} :</strong> {formatValue(client?.postal_code)}</p>
              <p className="convention-field"><strong>{t('email')} :</strong> {formatValue(client?.contact_mail)}</p>
              <p className="convention-field"><strong>{t('phone')} :</strong> {formatValue(client?.contact_phone)}</p>
            </div>
          </div>
        </section>

        <section className="convention-section">
          <h3>{t('conventionLegalTitle')}</h3>
          {Array.isArray(conventionParagraphs) && conventionParagraphs.map((paragraph, index) => (
            <p className="convention-paragraph" key={index}>{paragraph}</p>
          ))}
        </section>

        <section className="convention-section">
          <h3>{t('conventionSelectedToolsTitle')}</h3>
          {selectedToolKeys.length === 0 ? (
            <div className="empty-state">{t('conventionNoSelectedTool')}</div>
          ) : (
            <div className="convention-tools-grid">
              {selectedToolKeys.map((tool) => (
                <div className="convention-tool-card" key={tool}>
                  <h4>{t(TOOL_TRANSLATION_KEYS[tool] || tool)}</h4>
                  <ul className="convention-list">
                    {getToolParams(tool).map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="convention-section">
          <h3>{t('conventionScopeTitle')}</h3>
          {targets.length === 0 ? (
            <div className="empty-state">{t('noValidatedTarget')}</div>
          ) : (
            <table className="convention-table">
              <thead>
                <tr>
                  <th>{t('targetIp')}</th>
                  <th>{t('ports')}</th>
                </tr>
              </thead>
              <tbody>
                {targets.map((target) => (
                  <tr key={target.id}>
                    <td>{target.ip}</td>
                    <td>{target.true_cmd_port || t('none')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <p className="convention-legal-note">{t('conventionPhysicalSignatureNotice')}</p>

        <div className="convention-signature-grid pdf-only">
          <div className="signature-box">{t('auditorSignatureBox')}</div>
          <div className="signature-box">{t('clientSignatureBox')}</div>
        </div>
      </div>

      {isSigned ? (
        <div className="actions-row screen-only">
          <button className="btn-secondary" onClick={exportPdf}>{t('exportPdf')}</button>
          <div className="status-badge signed">{t('conventionAlreadySigned')}</div>
        </div>
      ) : (
        <div className="actions-row screen-only convention-actions-row">
          <button className="btn-secondary" onClick={exportPdf}>{t('exportPdf')}</button>
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
        <p className="muted-text screen-only">{t('signConventionNeedTarget')}</p>
      )}
    </div>
  );
}


