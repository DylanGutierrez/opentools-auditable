import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';
import GuideButton from './GuideButton';

export default function Header() {
  const [username, setUsername] = useState("");
  const { t, i18n } = useTranslation();

  // Récupération de l'utilisateur connecté
  useEffect(() => {
    axios.get(`${API_URL}/config`)
      .then((res) => setUsername(res.data.username || ""))
      .catch((err) => {
        console.error(t('logConfigLoadError'), err);
        toast.error(t('toastConfigLoadError'));
      });
  }, [t]);

  return (
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
          <GuideButton />

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
  );
}
