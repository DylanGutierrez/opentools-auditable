import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function ClientForm({ initialData, submitLabel, onSubmit }) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState(initialData);

  useEffect(() => {
    setFormData(initialData);
  }, [initialData]);

  // Gestion simple de la saisie du client
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const submit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={submit} className="form-card">
      <div className="form-grid">
        <div className="form-group">
          <label className="form-label">{t('companyNameLabel')}</label>
          <input
            type="text"
            name="company_name"
            placeholder={t('companyNamePlaceholder')}
            value={formData.company_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('managerLabel')}</label>
          <input
            type="text"
            name="dirigeant"
            placeholder={t('managerPlaceholder')}
            value={formData.dirigeant}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group full-width">
          <label className="form-label">{t('addressLabel')}</label>
          <input
            type="text"
            name="adresse"
            placeholder={t('addressPlaceholder')}
            value={formData.adresse}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('postalCodeLabel')}</label>
          <input
            type="text"
            name="postal_code"
            placeholder={t('postalCodePlaceholder')}
            value={formData.postal_code}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">{t('phoneLabel')}</label>
          <input
            type="text"
            name="contact_phone"
            placeholder={t('phonePlaceholder')}
            value={formData.contact_phone}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group full-width">
          <label className="form-label">{t('emailLabel')}</label>
          <input
            type="email"
            name="contact_mail"
            placeholder={t('emailPlaceholder')}
            value={formData.contact_mail}
            onChange={handleChange}
            required
          />
        </div>
      </div>

      <div className="actions-row">
        <button className="btn-primary" type="submit">{submitLabel}</button>
      </div>
    </form>
  );
}

