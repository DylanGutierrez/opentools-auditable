import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';

// Ne pas oublier de rajouter ces valeurs dans les Json i18n.
const OUTPUT_COMMON = ['', 'htm', 'sql', 'txt', 'json', 'xml', 'all'];
const OUTPUT_NMAP = ['', 'xml', 'txt', 'all'];
const NIKTO_TUNING_OPTIONS = [
  ['1', 'Interesting File / Seen in logs'],
  ['2', 'Misconfiguration / Default File'],
  ['3', 'Information Disclosure'],
  ['4', 'Injection (XSS/Script/HTML)'],
  ['5', 'Remote File Retrieval - Inside Web Root'],
  ['6', 'Denial of Service'],
  ['7', 'Remote File Retrieval - Server Wide'],
  ['8', 'Command Execution / Remote Shell'],
  ['9', 'SQL Injection'],
  ['0', 'File Upload'],
  ['a', 'Authentication Bypass'],
  ['b', 'Software Identification'],
  ['c', 'Remote Source Inclusion'],
  ['d', 'WebService']
];
const NUCLEI_SEVERITIES = ['info', 'low', 'medium', 'high', 'critical'];

export default function Settings() {
  const { t } = useTranslation();
  const { auditId } = useParams();
  const [loading, setLoading] = useState(true);
  const [isSigned, setIsSigned] = useState(false);
  const [settings, setSettings] = useState(null);

  // Vérification des paramètres
  const loadSettings = () => {
    axios.get(`${API_URL}/settings/${auditId}`)
      .then((res) => {
        setIsSigned(!!res.data.signed);
        setSettings(res.data.settings || null);
      })
      .catch((err) => {
        console.error(t('logSettingsLoadError'), err);
        toast.error(err.response?.data?.error || t('toastSettingsLoadError'));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSettings();
  }, [auditId, t]);

  // Mise à jour des paramètres d'un outil
  const updateTool = (tool, values) => {
    const nextSettings = {
      ...settings,
      [tool]: {
        ...settings[tool],
        ...values
      }
    };
    setSettings(nextSettings);

    axios.put(`${API_URL}/settings/${auditId}`, {
      tool,
      values: nextSettings[tool]
    })
      .then((res) => {
        setSettings(res.data.settings || nextSettings);
        toast.success(res.data.message || t('toastSettingsUpdated'));
      })
      .catch((err) => {
        console.error(t('logSettingsUpdateError'), err);
        toast.error(err.response?.data?.error || t('toastSettingsUpdateError'));
        loadSettings();
      });
  };

  // Tuning Nikto
  const toggleTuning = (code) => {
    const current = settings.nikto.tuning_option || '';
    const hasCode = current.includes(code);
    const next = hasCode
      ? current.split('').filter((item) => item !== code).join('')
      : `${current}${code}`;
    updateTool('nikto', { tuning_option: next });
  };

  // Criticités Nuclei
  const toggleSeverity = (severity) => {
    const current = (settings.nuclei.severity || '').split(',').filter(Boolean);
    const hasSeverity = current.includes(severity);
    const next = hasSeverity
      ? current.filter((item) => item !== severity)
      : [...current, severity];

    if (next.length === 0) {
      toast.warning(t('toastNucleiSeverityRequired'));
      return;
    }

    updateTool('nuclei', { severity: next.join(',') });
  };

  if (loading) return <p className="loader-text">{t('loading')}</p>;
  if (!settings) return <div className="empty-state">{t('noSettingsData')}</div>;

  const renderOutputSelect = (tool, options) => (
    <select
      value={settings[tool].output_file || ''}
      onChange={(e) => updateTool(tool, { output_file: e.target.value })}
      disabled={isSigned}
    >
      {options.map((option) => (
        <option key={option || 'none'} value={option}>{option || t('noExport')}</option>
      ))}
    </select>
  );

  return (
    <div className="page-card settings-page-card">
      <h2 className="page-title settings-page-title">{t('settingsTitle')}</h2>
      <p className="page-subtitle">{t('settingsSubtitle')}</p>

      <div className={`status-badge ${isSigned ? 'signed' : 'unsigned'}`}>
        {isSigned ? t('settingsLocked') : t('settingsEditable')}
      </div>

      <div className="settings-grid">
        <div className="settings-card">
          <h3>{t('toolNmap')}</h3>
          <div className="form-group">
            <label className="form-label">{t('aggressiveness')} : {settings.nmap.aggressiveness}</label>
            <input
              type="range"
              min="0"
              max="9"
              value={settings.nmap.aggressiveness ?? 0}
              disabled={isSigned}
              onChange={(e) => updateTool('nmap', { aggressiveness: Number(e.target.value) })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">{t('outputFormat')}</label>
            {renderOutputSelect('nmap', OUTPUT_NMAP)}
          </div>
        </div>

        <div className="settings-card">
          <h3>{t('toolNikto')}</h3>
          <div className="form-group">
            <label className="form-label">{t('aggressiveness')} : {settings.nikto.aggressiveness}</label>
            <input
              type="range"
              min="0"
              max="9"
              value={settings.nikto.aggressiveness ?? 0}
              disabled={isSigned}
              onChange={(e) => updateTool('nikto', { aggressiveness: Number(e.target.value) })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">{t('outputFormat')}</label>
            {renderOutputSelect('nikto', OUTPUT_COMMON)}
          </div>
          <div className="form-group full-width">
            <label className="form-label">{t('niktoTuning')}</label>
            <div className="checkbox-row compact-checkboxes">
              {NIKTO_TUNING_OPTIONS.map(([code, label]) => (
                <label className="checkbox-item" key={code}>
                  <input
                    type="checkbox"
                    checked={(settings.nikto.tuning_option || '').includes(code)}
                    disabled={isSigned}
                    onChange={() => toggleTuning(code)}
                  />
                  <span><strong>{code}</strong> - {label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="settings-card">
          <h3>{t('toolWPScan')}</h3>
          <div className="checkbox-row">
            <label className="checkbox-item">
              <input
                type="checkbox"
                checked={!!settings.wpscan.aggressiveness}
                disabled={isSigned}
                onChange={(e) => updateTool('wpscan', { aggressiveness: e.target.checked })}
              />
              {t('aggressiveMode')}
            </label>
          </div>
          <div className="form-group">
            <label className="form-label">{t('outputFormat')}</label>
            {renderOutputSelect('wpscan', OUTPUT_COMMON)}
          </div>
          <div className="form-group">
            <label className="form-label">{t('wpscanEnumeration')}</label>
            <select
              value={settings.wpscan.enumeration_mode || 'vulnerable'}
              disabled={isSigned}
              onChange={(e) => updateTool('wpscan', { enumeration_mode: e.target.value })}
            >
              <option value="vulnerable">{t('wpscanEnumVulnerable')}</option>
              <option value="complete">{t('wpscanEnumComplete')}</option>
            </select>
            <p className="muted-text">{settings.wpscan.enumeration_option}</p>
          </div>
        </div>

        <div className="settings-card">
          <h3>{t('toolNuclei')}</h3>
          <div className="form-group">
            <label className="form-label">{t('aggressiveness')} : {settings.nuclei.aggressiveness}</label>
            <input
              type="range"
              min="0"
              max="9"
              value={settings.nuclei.aggressiveness ?? 0}
              disabled={isSigned}
              onChange={(e) => updateTool('nuclei', { aggressiveness: Number(e.target.value) })}
            />
            <p className="muted-text">{t('nucleiRateLimitHelp', { value: settings.nuclei.aggressiveness })}</p>
          </div>
          <div className="form-group">
            <label className="form-label">{t('outputFormat')}</label>
            {renderOutputSelect('nuclei', OUTPUT_COMMON)}
          </div>
          <div className="form-group full-width">
            <label className="form-label">{t('nucleiSeverity')}</label>
            <div className="checkbox-row">
              {NUCLEI_SEVERITIES.map((severity) => (
                <label className="checkbox-item" key={severity}>
                  <input
                    type="checkbox"
                    checked={(settings.nuclei.severity || '').split(',').includes(severity)}
                    disabled={isSigned}
                    onChange={() => toggleSeverity(severity)}
                  />
                  {severity}
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

