// Construction des étapes du guide selon la page courante

function getGuidePageKey(pathname) {
  if (pathname === '/' || pathname === '/home') return 'home';
  if (pathname === '/client') return 'client';
  if (pathname === '/client/add') return 'clientAdd';
  if (pathname === '/client/edit') return 'clientEdit';
  if (pathname.includes('/convention')) return 'convention';
  if (pathname.includes('/analyses')) return 'analyses';
  if (pathname.includes('/settings')) return 'settings';
  if (pathname.includes('/logs')) return 'logs';
  if (pathname.includes('/audit')) return 'audit';
  return 'default';
}

function isGuideElementAvailable(selector) {
  const element = document.querySelector(selector);
  if (!element) return false;
  return !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length);
}

function guideStep(element, title, description, side = 'bottom', align = 'center') {
  return {
    element,
    popover: {
      title,
      description,
      side,
      align
    }
  };
}

export function buildGuideSteps(t, pathname) {
  const pageKey = getGuidePageKey(pathname);

  const commonSteps = [
    guideStep('.brand-block', t('guideStepHeaderTitle'), t('guideStepHeaderDescription')),
    guideStep('.nav-links', t('guideStepNavigationTitle'), t('guideStepNavigationDescription')),
    guideStep('.language-select', t('guideStepLanguageTitle'), t('guideStepLanguageDescription'), 'bottom', 'end')
  ];

  const pageSteps = {
    home: [
      guideStep('.page-title', t('guideHomeTitleTitle'), t('guideHomeTitleDescription')),
      guideStep('.home-steps', t('guideHomeStepsTitle'), t('guideHomeStepsDescription'), 'top')
    ],
    client: [
      guideStep('.info-grid', t('guideClientInfoTitle'), t('guideClientInfoDescription'), 'top'),
      guideStep('.status-badge', t('guideClientStatusTitle'), t('guideClientStatusDescription')),
      guideStep('.actions-row', t('guideClientActionsTitle'), t('guideClientActionsDescription'), 'top')
    ],
    clientAdd: [
      guideStep('.form-card', t('guideClientFormTitle'), t('guideClientFormDescription'), 'top')
    ],
    clientEdit: [
      guideStep('.form-card', t('guideClientEditFormTitle'), t('guideClientEditFormDescription'), 'top')
    ],
    convention: [
      guideStep('.convention-document', t('guideConventionDocumentTitle'), t('guideConventionDocumentDescription'), 'top'),
      guideStep('.convention-party-grid', t('guideConventionPartiesTitle'), t('guideConventionPartiesDescription'), 'top'),
      guideStep('.convention-tools-grid', t('guideConventionToolsTitle'), t('guideConventionToolsDescription'), 'top'),
      guideStep('.convention-table', t('guideConventionScopeTitle'), t('guideConventionScopeDescription'), 'top'),
      guideStep('.convention-actions-row', t('guideConventionActionsTitle'), t('guideConventionActionsDescription'), 'top')
    ],
    analyses: [
      guideStep('.checkbox-row', t('guideAnalysesToolsTitle'), t('guideAnalysesToolsDescription'), 'top'),
      guideStep('.inline-form', t('guideAnalysesScopeFormTitle'), t('guideAnalysesScopeFormDescription'), 'top'),
      guideStep('.target-list', t('guideAnalysesTargetsTitle'), t('guideAnalysesTargetsDescription'), 'top'),
      guideStep('.actions-row', t('guideAnalysesLaunchTitle'), t('guideAnalysesLaunchDescription'), 'top')
    ],
    settings: [
      guideStep('.settings-grid', t('guideSettingsGridTitle'), t('guideSettingsGridDescription'), 'top'),
      guideStep('.settings-card', t('guideSettingsCardTitle'), t('guideSettingsCardDescription'), 'top'),
      guideStep('.compact-checkboxes', t('guideSettingsNiktoTitle'), t('guideSettingsNiktoDescription'), 'top')
    ],
    logs: [
      guideStep('.logs-filter', t('guideLogsFilterTitle'), t('guideLogsFilterDescription'), 'right'),
      guideStep('.log-entry', t('guideLogsEntriesTitle'), t('guideLogsEntriesDescription'), 'top'),
      guideStep('.log-content', t('guideLogsContentTitle'), t('guideLogsContentDescription'), 'top')
    ],
    audit: [
      guideStep('.audit-vuln-card', t('guideAuditVulnsTitle'), t('guideAuditVulnsDescription'), 'top'),
      guideStep('.remediation-editor', t('guideAuditRemediationTitle'), t('guideAuditRemediationDescription'), 'top'),
      guideStep('.audit-export-actions', t('guideAuditExportsTitle'), t('guideAuditExportsDescription'), 'top')
    ],
    default: [
      guideStep('.page-card', t('guideDefaultPageTitle'), t('guideDefaultPageDescription'), 'top')
    ]
  };

  return [...commonSteps, ...(pageSteps[pageKey] || pageSteps.default)]
    .filter((step) => isGuideElementAvailable(step.element));
}

