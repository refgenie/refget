import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore.js';
import { APINav } from '../components/APINav.jsx';
import { CompliancePage } from './CompliancePage.jsx';

const APICompliance = () => {
  const [searchParams] = useSearchParams();
  const { apiUrl, probeApi } = useApiExplorerStore();
  const urlParam = searchParams.get('url');

  useEffect(() => {
    if (urlParam && !apiUrl) {
      probeApi(urlParam).catch(() => {});
    }
  }, [urlParam]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <APINav active="compliance" />
      <CompliancePage />
    </div>
  );
};

export { APICompliance };
