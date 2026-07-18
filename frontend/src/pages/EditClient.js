import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import API_URL from '../config/api';
import ClientForm from '../components/ClientForm';

export default function EditClient() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [client, setClient] = useState(null);

  // Vérification que le client peut encore être modifié.
  useEffect(() => {
    axios.get(`${API_URL}/client`)
      .then((res) => {
        if (!res.data) {
          toast.error(t('toastNoClientToEdit'));
          navigate('/client');
          return;
        }
        if (res.data.convention_signed) {
          toast.error(t('toastClientLocked'));
          navigate('/client');
          return;
        }
        setClient(res.data);
      })
      .catch((err) => {
        console.error(t('logClientLoadError'), err);
        toast.error(err.response?.data?.error || t('toastClientLoadError'));
      });
  }, [navigate, t]);

  // Modification du client
  const handleSubmit = (formData) => {
    axios.put(`${API_URL}/client`, formData)
      .then((res) => {
        toast.success(res.data.message || t('toastClientUpdated'));
        navigate('/client');
      })
      .catch((err) => {
        console.error(t('logClientUpdateError'), err);
        toast.error(err.response?.data?.error || t('toastClientUpdateError'));
      });
  };

  if (!client) return <p className="loader-text">{t('loading')}</p>;

  return (
    <div className="page-card">
      <h2 className="page-title">{t('editClientTitle')}</h2>
      <ClientForm
        initialData={client}
        submitLabel={t('update')}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

