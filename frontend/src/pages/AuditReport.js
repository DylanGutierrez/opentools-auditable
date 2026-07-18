import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';

export default function AuditReport() {
  const { t, i18n } = useTranslation();
  const { auditId } = useParams();
  const [loading, setLoading] = useState(true);
  const [auditData, setAuditData] = useState(null);
  const [remediationDrafts, setRemediationDrafts] = useState({});
  const [savingRemediationId, setSavingRemediationId] = useState(null);

  // Récupération des vulnérabilités
  useEffect(() => {
    axios.get(`${API_URL}/audit/${auditId}/report`)
      .then((res) => {
        const data = res.data;
        setAuditData(data);

        const drafts = {};
        (data.vulnerabilities || []).forEach((vuln) => {
          drafts[vuln.id] = vuln.remediation || '';
        });
        setRemediationDrafts(drafts);
      })
      .catch((err) => {
        console.error(t('logAuditLoadError'), err);
        toast.error(err.response?.data?.error || t('toastAuditLoadError'));
      })
      .finally(() => setLoading(false));
  }, [auditId, t]);

  const formatPercentage = (value) => {
    if (value === null || value === undefined || value === '') {
      return t('notAvailable');
    }

    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return t('notAvailable');
    }

    return `${numericValue.toFixed(2)} %`;
  };

  const getSeverityClassName = (value) => {
    const numericValue = Number(value);

    if (!Number.isFinite(numericValue)) {
      return 'severity-unknown';
    }

    if (numericValue >= 9) {
      return 'severity-critical';
    }

    if (numericValue >= 7) {
      return 'severity-high';
    }

    if (numericValue >= 4) {
      return 'severity-medium';
    }

    if (numericValue > 0) {
      return 'severity-low';
    }

    return 'severity-none';
  };


  const escapeHtml = (value) => String(value ?? '').replace(
    /[&<>"']/g,
    (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[char])
  );

  const normalizeFilePart = (value) => String(value || 'audit')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'audit';

  // Préparation des exports HTML / PDF.
  const buildAuditExportHtml = ({ autoPrint = false } = {}) => {
    const audit = auditData?.audit || {};
    const vulnerabilities = auditData?.vulnerabilities || [];
    const generatedAt = new Date().toLocaleString(i18n.language || 'fr');

    const vulnerabilityCards = vulnerabilities.length > 0
      ? vulnerabilities.map((vuln, index) => {
          const remediation = remediationDrafts[vuln.id] || vuln.remediation || t('noRemediation');
          const severityClass = getSeverityClassName(vuln.criticity);

          return `
            <article class="vulnerability-card">
              <header class="vulnerability-header">
                <div>
                  <p class="vulnerability-index">${escapeHtml(t('auditExportVulnerabilityLabel', { number: index + 1 }))}</p>
                  <h2>${escapeHtml(vuln.CVE || t('notAvailable'))}</h2>
                </div>
                <div class="badge-row">
                  <span class="audit-badge audit-badge-primary">${escapeHtml(t('cve'))} : ${escapeHtml(vuln.CVE || t('notAvailable'))}</span>
                  <span class="audit-badge audit-badge-primary">${escapeHtml(t('cvss'))} : ${escapeHtml(vuln.CVSS || t('notAvailable'))}</span>
                  <span class="audit-badge ${severityClass}">${escapeHtml(t('criticality'))} : ${escapeHtml(vuln.criticity ?? t('notAvailable'))}</span>
                  <span class="audit-badge audit-badge-success">${escapeHtml(t('epss'))} : ${escapeHtml(formatPercentage(vuln.EPSS))}</span>
                </div>
              </header>

              <div class="vulnerability-table-wrap">
                <table class="vulnerability-table">
                  <tbody>
                    <tr>
                      <th>${escapeHtml(t('description'))}</th>
                      <td>${escapeHtml(vuln.description || t('noDescription'))}</td>
                    </tr>
                    <tr>
                      <th>${escapeHtml(t('remediation'))}</th>
                      <td>${escapeHtml(remediation)}</td>
                    </tr>
                    <tr>
                      <th>${escapeHtml(t('epss'))}</th>
                      <td>
                        <strong>${escapeHtml(formatPercentage(vuln.EPSS))}</strong>
                        <span class="muted-inline">${escapeHtml(t('epssPercentile'))} : ${escapeHtml(formatPercentage(vuln.EPSS_percentile))}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          `;
        }).join('')
      : `<div class="empty-state">${escapeHtml(t('noVulnerability'))}</div>`;

    return `<!doctype html>
<html lang="${escapeHtml((i18n.language || 'fr').slice(0, 2))}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(t('auditExportDocumentTitle', { auditId }))}</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card: #ffffff;
      --card-soft: #f8fafc;
      --text: #0f172a;
      --muted: #64748b;
      --border: #e2e8f0;
      --primary: #2563eb;
      --primary-soft: #dbeafe;
      --success: #047857;
      --success-soft: #ecfdf5;
      --critical: #991b1b;
      --critical-soft: #fee2e2;
      --high: #b91c1c;
      --high-soft: #fee2e2;
      --medium: #92400e;
      --medium-soft: #fef3c7;
      --low: #166534;
      --low-soft: #dcfce7;
      --shadow: 0 12px 35px rgba(15, 23, 42, 0.12);
      --radius: 16px;
    }

    * {
      box-sizing: border-box;
      overflow-wrap: break-word;
      word-break: normal;
      hyphens: none;
    }

    body {
      margin: 0;
      font-family: Inter, Arial, Helvetica, sans-serif;
      background: radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 25%), linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
      color: var(--text);
      line-height: 1.55;
    }

    .export-shell {
      max-width: 1180px;
      margin: 32px auto;
      padding: 0 20px 40px;
    }

    .export-document {
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid rgba(226, 232, 240, 0.9);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 32px;
    }

    .export-hero {
      text-align: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 24px;
    }

    .export-eyebrow {
      margin: 0 0 8px;
      color: var(--primary);
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.82rem;
    }

    h1 {
      margin: 0;
      font-size: 2.1rem;
      color: var(--text);
    }

    .export-subtitle {
      margin: 10px auto 0;
      color: var(--muted);
      max-width: 760px;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }

    .info-item {
      background: var(--card-soft);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px 16px;
    }

    .info-label {
      display: block;
      font-size: 0.82rem;
      color: var(--muted);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-weight: 700;
    }

    .info-value {
      font-size: 1rem;
      font-weight: 700;
    }

    .section-title {
      margin: 28px 0 14px;
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--text);
      text-align: center;
    }

    .vulnerability-card {
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
      padding: 22px;
      margin: 0 0 22px;
      break-inside: avoid;
      page-break-inside: avoid;
    }

    .vulnerability-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      flex-wrap: wrap;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
      margin-bottom: 16px;
    }

    .vulnerability-index {
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .vulnerability-header h2 {
      margin: 0;
      font-size: 1.45rem;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
      max-width: 650px;
    }

    .audit-badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.88rem;
      font-weight: 800;
      white-space: nowrap;
    }

    .audit-badge-primary {
      background: var(--primary-soft);
      color: #1d4ed8;
    }

    .audit-badge-success {
      background: var(--success-soft);
      color: var(--success);
    }

    .severity-critical,
    .severity-high {
      background: var(--high-soft);
      color: var(--high);
    }

    .severity-medium {
      background: var(--medium-soft);
      color: var(--medium);
    }

    .severity-low,
    .severity-none {
      background: var(--low-soft);
      color: var(--low);
    }

    .severity-unknown {
      background: #e2e8f0;
      color: #334155;
    }

    .vulnerability-table-wrap {
      overflow-x: auto;
    }

    .vulnerability-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
    }

    .vulnerability-table th,
    .vulnerability-table td {
      border-bottom: 1px solid var(--border);
      padding: 14px 16px;
      text-align: left;
      vertical-align: top;
    }

    .vulnerability-table tr:last-child th,
    .vulnerability-table tr:last-child td {
      border-bottom: none;
    }

    .vulnerability-table th {
      width: 190px;
      background: #eff6ff;
      color: #0f172a;
      font-weight: 800;
    }

    .muted-inline {
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .empty-state {
      text-align: center;
      padding: 26px;
      border: 1px dashed #cbd5e1;
      border-radius: 14px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.6);
      font-weight: 700;
    }

    .export-footer {
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.9rem;
      text-align: center;
    }

    @page {
      size: A4;
      margin: 14mm;
    }

    @media print {
      body {
        background: #ffffff;
      }

      .export-shell {
        max-width: none;
        margin: 0;
        padding: 0;
      }

      .export-document {
        border: none;
        box-shadow: none;
        border-radius: 0;
        padding: 0;
      }

      .info-item,
      .vulnerability-card,
      .export-hero,
      .export-footer {
        break-inside: avoid;
        page-break-inside: avoid;
      }

      .vulnerability-card {
        box-shadow: none;
      }
    }
  </style>
</head>
<body>
  <main class="export-shell">
    <article class="export-document">
      <header class="export-hero">
        <p class="export-eyebrow">OpenTools / Auditable</p>
        <h1>${escapeHtml(t('auditExportTitle'))}</h1>
        <p class="export-subtitle">${escapeHtml(t('auditExportSubtitle', { date: generatedAt }))}</p>
      </header>

      <section class="info-grid" aria-label="${escapeHtml(t('auditExportContext'))}">
        <div class="info-item">
          <span class="info-label">${escapeHtml(t('client'))}</span>
          <span class="info-value">${escapeHtml(audit.company_name || t('notAvailable'))}</span>
        </div>
        <div class="info-item">
          <span class="info-label">${escapeHtml(t('manager'))}</span>
          <span class="info-value">${escapeHtml(audit.dirigeant || t('notAvailable'))}</span>
        </div>
        <div class="info-item">
          <span class="info-label">${escapeHtml(t('audit'))}</span>
          <span class="info-value">${escapeHtml(audit.title || t('notAvailable'))}</span>
        </div>
        <div class="info-item">
          <span class="info-label">${escapeHtml(t('convention'))}</span>
          <span class="info-value">${escapeHtml(audit.convention_signed ? t('signed') : t('unsigned'))}</span>
        </div>
      </section>

      <section>
        <h2 class="section-title">${escapeHtml(t('auditExportVulnerabilitiesTitle'))}</h2>
        ${vulnerabilityCards}
      </section>

      <footer class="export-footer">
        ${escapeHtml(t('auditExportFooter'))}
      </footer>
    </article>
  </main>
  ${autoPrint ? `<script>window.addEventListener('load', function () { setTimeout(function () { window.focus(); window.print(); }, 450); });</script>` : ''}
</body>
</html>`;
  };

  const getAuditExportFilename = (extension) => {
    const audit = auditData?.audit || {};
    const company = normalizeFilePart(audit.company_name || 'client');
    const datePart = new Date().toISOString().slice(0, 10);
    return `audit-${auditId}-${company}-${datePart}.${extension}`;
  };

  const handleExportHtml = () => {
    try {
      const html = buildAuditExportHtml({ autoPrint: false });
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');

      link.href = url;
      link.download = getAuditExportFilename('html');
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      toast.success(t('toastHtmlExported'));
    } catch (error) {
      console.error(t('logHtmlExportError'), error);
      toast.error(t('toastHtmlExportError'));
    }
  };

  const handleExportPdf = () => {
    let pdfWindow = null;

    try {
      pdfWindow = window.open('', '_blank');

      if (!pdfWindow) {
        toast.error(t('toastPdfPopupBlocked'));
        return;
      }

      const html = buildAuditExportHtml({ autoPrint: true });
      pdfWindow.document.open();
      pdfWindow.document.write(html);
      pdfWindow.document.close();
    } catch (error) {
      console.error(t('logPdfExportError'), error);
      toast.error(t('toastPdfExportError'));

      if (pdfWindow && !pdfWindow.closed) {
        pdfWindow.close();
      }
    }
  };

  const handleRemediationChange = (vulnerabilityId, value) => {
    setRemediationDrafts((current) => ({
      ...current,
      [vulnerabilityId]: value
    }));
  };

  // Mise à jour des remédiations.
  const handleRemediationUpdate = (vulnerabilityId) => {
    const remediation = remediationDrafts[vulnerabilityId] || '';
    setSavingRemediationId(vulnerabilityId);

    axios.put(
      `${API_URL}/audit/${auditId}/vulnerabilities/${vulnerabilityId}/remediation`,
      { remediation }
    )
      .then((res) => {
        const savedRemediation = res.data.remediation || '';

        setRemediationDrafts((current) => ({
          ...current,
          [vulnerabilityId]: savedRemediation
        }));

        setAuditData((current) => ({
          ...current,
          vulnerabilities: (current.vulnerabilities || []).map((vuln) => (
            vuln.id === vulnerabilityId
              ? { ...vuln, remediation: savedRemediation }
              : vuln
          ))
        }));

        toast.success(res.data.message || t('toastRemediationUpdated'));
      })
      .catch((err) => {
        console.error(t('logRemediationUpdateError'), err);
        toast.error(
          err.response?.data?.error || t('toastRemediationUpdateError')
        );
      })
      .finally(() => setSavingRemediationId(null));
  };

  if (loading) return <p className="loader-text">{t('loading')}</p>;
  if (!auditData) return <div className="empty-state">{t('noAuditData')}</div>;

  const { audit, vulnerabilities } = auditData;

  return (
    <div className="page-card">
      <h2 className="page-title audit-page-title">{t('auditTitle')}</h2>

      <div className="info-grid">
        <div className="info-item"><span className="info-label">{t('client')}</span><span className="info-value">{audit.company_name}</span></div>
        <div className="info-item"><span className="info-label">{t('manager')}</span><span className="info-value">{audit.dirigeant}</span></div>
        <div className="info-item"><span className="info-label">{t('audit')}</span><span className="info-value">{audit.title}</span></div>
        <div className="info-item"><span className="info-label">{t('convention')}</span><span className="info-value">{audit.convention_signed ? t('signed') : t('unsigned')}</span></div>
      </div>

      {!vulnerabilities || vulnerabilities.length === 0 ? (
        <div className="empty-state">{t('noVulnerability')}</div>
      ) : (
        vulnerabilities.map((vuln) => {
          const isSaving = savingRemediationId === vuln.id;

          return (
            <div key={vuln.id} className="audit-vuln-card">
              <div className="audit-vuln-head">
                <div className="audit-pill">{t('cve')} : {vuln.CVE || t('notAvailable')}</div>
                <div className="audit-pill">{t('cvss')} : {vuln.CVSS || t('notAvailable')}</div>
                <div className={`audit-pill audit-pill-severity ${getSeverityClassName(vuln.criticity)}`}>
                  {t('criticality')} : {vuln.criticity ?? t('notAvailable')}
                </div>
                <div className="audit-pill audit-pill-epss">
                  {t('epss')} : {formatPercentage(vuln.EPSS)}
                </div>
              </div>

              <div className="table-wrapper">
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>{t('cve')}</th>
                      <th>{t('criticality')}</th>
                      <th>{t('description')}</th>
                      <th>{t('remediation')}</th>
                      <th>{t('epss')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{vuln.CVE || t('notAvailable')}</td>
                      <td>{vuln.criticity ?? t('notAvailable')}</td>
                      <td>{vuln.description || t('noDescription')}</td>
                      <td>{remediationDrafts[vuln.id] || vuln.remediation || t('noRemediation')}</td>
                      <td>
                        <div className="epss-cell">
                          <strong>{formatPercentage(vuln.EPSS)}</strong>
                          <span>
                            {t('epssPercentile')} : {formatPercentage(vuln.EPSS_percentile)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="remediation-editor">
                <label
                  className="form-label"
                  htmlFor={`remediation-${vuln.id}`}
                >
                  {t('remediation')}
                </label>
                <textarea
                  id={`remediation-${vuln.id}`}
                  className="remediation-input"
                  value={remediationDrafts[vuln.id] || ''}
                  onChange={(event) => (
                    handleRemediationChange(vuln.id, event.target.value)
                  )}
                  placeholder={t('remediationPlaceholder')}
                  rows={5}
                  maxLength={10000}
                  disabled={isSaving}
                />
                <div className="remediation-actions">
                  <span className="remediation-counter">
                    {(remediationDrafts[vuln.id] || '').length} / 10000
                  </span>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => handleRemediationUpdate(vuln.id)}
                    disabled={isSaving}
                  >
                    {isSaving ? t('saving') : t('updateRemediation')}
                  </button>
                </div>
              </div>
            </div>
          );
        })
      )}

      <div className="audit-export-actions">
        <button
          type="button"
          className="btn-secondary btn-export-html"
          onClick={handleExportHtml}
        >
          {t('exportHtml')}
        </button>
        <button
          type="button"
          className="btn-primary btn-export-pdf"
          onClick={handleExportPdf}
        >
          {t('exportPdf')}
        </button>
      </div>
    </div>
  );
}


