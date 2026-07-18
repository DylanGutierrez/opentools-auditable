// Paramètres utilisés pour construire la convention et son export PDF

export const DEFAULT_AUDIT_TOOLS = { nmap: true, wpscan: false, nikto: false, nuclei: false };
export const TOOL_TRANSLATION_KEYS = {
  nmap: 'toolNmap',
  wpscan: 'toolWPScan',
  nikto: 'toolNikto',
  nuclei: 'toolNuclei'
};

export function readSelectedAuditTools(auditId) {
  try {
    const savedTools = localStorage.getItem(`audit-tools-${auditId}`);
    return savedTools ? { ...DEFAULT_AUDIT_TOOLS, ...JSON.parse(savedTools) } : DEFAULT_AUDIT_TOOLS;
  } catch {
    return DEFAULT_AUDIT_TOOLS;
  }
}

export function buildConventionPrintStyles() {
  return `
    @page { size: A4; margin: 18mm 16mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: #ffffff; color: #0f172a; }
    body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; line-height: 1.45; }
    .convention-document { width: 100%; max-width: none; margin: 0; padding: 0; background: #ffffff; box-shadow: none; border: none; color: #0f172a; word-break: normal; overflow-wrap: break-word; hyphens: none; }
    .convention-doc-header { border-bottom: 2px solid #0f172a; padding-bottom: 14px; margin-bottom: 18px; }
    .convention-doc-title { margin: 0 0 6px; font-size: 20pt; line-height: 1.2; }
    .convention-doc-meta { display: flex; flex-wrap: wrap; gap: 8px; color: #334155; font-size: 10pt; }
    .convention-section { margin: 18px 0; break-inside: avoid; page-break-inside: avoid; }
    .convention-section h3 { margin: 0 0 10px; font-size: 14pt; border-bottom: 1px solid #cbd5e1; padding-bottom: 5px; }
    .convention-paragraph { margin: 0 0 10px; text-align: justify; }
    .convention-party-grid, .convention-tools-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .convention-party-card, .convention-tool-card { border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; break-inside: avoid; page-break-inside: avoid; }
    .convention-party-card h4, .convention-tool-card h4 { margin: 0 0 8px; font-size: 12pt; }
    .convention-list { margin: 0; padding-left: 18px; }
    .convention-list li { margin-bottom: 5px; }
    .convention-field { margin: 0 0 6px; }
    .convention-field strong { display: inline-block; min-width: 125px; }
    .convention-table { width: 100%; border-collapse: collapse; margin-top: 8px; table-layout: fixed; }
    .convention-table th, .convention-table td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; overflow-wrap: break-word; word-break: normal; }
    .convention-table th { background: #f1f5f9; }
    .convention-table tr { break-inside: avoid; page-break-inside: avoid; }
    .convention-legal-note { margin-top: 16px; padding: 10px; border: 1px solid #cbd5e1; background: #ffffff; font-weight: 700; break-inside: avoid; page-break-inside: avoid; }
    .pdf-only { display: grid !important; }
    .screen-only { display: none !important; }
    .convention-signature-grid { grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 24px; break-inside: avoid; page-break-inside: avoid; }
    .signature-box { height: 120px; border: 1px solid #0f172a; background: #ffffff; padding: 10px; display: flex; align-items: flex-start; justify-content: center; font-weight: 700; break-inside: avoid; page-break-inside: avoid; }
    p, li, td, th, h1, h2, h3, h4 { word-break: normal; overflow-wrap: break-word; hyphens: none; }
  `;
}

