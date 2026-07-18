import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';
import ClientForm from '../components/ClientForm';

export default function AddClient() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Vérification qu'un client n'existe pas déjà
  useEffect(() => {
    axios.get(`${API_URL}/client`)
      .then((res) => {
        if (res.data) {
          toast.error(t('toastClientAlreadyExists'));
          navigate('/client');
        }
      })
      .catch((err) => {
        console.error(t('logClientCheckError'), err);
      });
  }, [navigate, t]);

  // Création du client
  const handleSubmit = (formData) => {
    axios.post(`${API_URL}/client`, formData)
      .then(() => {
        toast.success(t('toastClientAdded'));
        navigate('/client');
      })
      .catch((err) => {
        console.error(t('logClientAddError'), err);
        toast.error(err.response?.data?.error || t('toastClientAddError'));
      });
  };

  return (
    <div className="page-card">
      <h2 className="page-title">{t('addClientTitle')}</h2>
      <ClientForm
        initialData={{
          company_name: '',
          dirigeant: '',
          adresse: '',
          postal_code: '',
          contact_mail: '',
          contact_phone: ''
        }}
        submitLabel={t('save')}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

