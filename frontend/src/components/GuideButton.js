import React from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';
import { buildGuideSteps } from '../utils/guideSteps';

export default function GuideButton() {
  const { t } = useTranslation();
  const location = useLocation();

  // Lancement du guide de la page courante, utilisation du thème de base.
  const startGuide = () => {
    const steps = buildGuideSteps(t, location.pathname);

    if (!steps.length) {
      toast.info(t('guideNoSteps'));
      return;
    }

    const guide = driver({
      showProgress: true,
      allowClose: true,
      animate: true,
      smoothScroll: true,
      popoverClass: 'auditable-driver-popover',
      nextBtnText: t('guideNext'),
      prevBtnText: t('guidePrevious'),
      doneBtnText: t('guideDone'),
      progressText: t('guideProgressText'),
      steps
    });

    guide.drive();
  };

  return (
    <button
      type="button"
      className="nav-link guide-nav-button"
      onClick={startGuide}
    >
      {t('guide')}
    </button>
  );
}

