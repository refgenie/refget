import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApiExplorerStore } from '../stores/apiExplorerStore';
import { APINav } from '../components/APINav';
import { SCIM } from './SCIM';

const APICompare = () => {
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
      <APINav active="compare" />
      <SCIM />
    </div>
  );
};

export { APICompare };
