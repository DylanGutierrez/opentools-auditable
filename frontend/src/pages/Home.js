import React from 'react';
import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
  // Récupération des étapes d'aide affichées sur l'accueil.
  const steps = t('homeSteps', { returnObjects: true });

  return (
    <div className="page-card">
      <h1 className="page-title">{t('homeAuditableTitle')}</h1>
      <p className="page-subtitle">{t('homeAuditableIntro')}</p>

      <h2 className="section-title">{t('homeHowToStart')}</h2>
      <div className="home-steps">
        {Array.isArray(steps) && steps.map((step, index) => (
          <div className="home-step" key={index}>
            <span className="home-step-number">{index + 1}</span>
            <p>{step}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

