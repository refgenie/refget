import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';

import './index.css';

import databio_logo from './assets/logo_databio_long.svg';
import seqcol_logo from './assets/seqcol_logo.svg';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/js/bootstrap.bundle.js';
import 'bootstrap-icons/font/bootstrap-icons.css';

import { CollectionView } from './pages/CollectionView.jsx';
import { PangenomeView } from './pages/PangenomeView.jsx';
import { AttributeView } from './pages/AttributeView.jsx';
import { DemoPage } from './pages/DemoPage.jsx';
import { SCIM } from './pages/SCIM.jsx';
import { SCOM } from './pages/SCOM.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { HPRCGenomes } from './pages/HPRCGenomes.jsx';
import { HumanReferencesView } from './pages/HumanReferences.jsx';
import { DigestPage } from './pages/DigestPage.jsx';
import { CompliancePage } from './pages/CompliancePage.jsx';

import {
  fetchServiceInfo,
  fetchPangenomeLevels,
  fetchSeqColList,
  fetchAllSeqCols,
  fetchCollectionLevels,
  fetchComparison,
  fetchAttribute,
} from './services/fetchData.jsx';

import { copyToClipboard } from './utilities';

import {
  Outlet,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useRouteError,
  useNavigate,
  useLocation,
} from 'react-router-dom';

import { API_BASE } from './utilities.jsx';

const Nav = () => {
  const navigate = useNavigate();
  const location = useLocation().pathname.substring(1) || '';

  return (
    <nav
      className='navbar navbar-expand-lg py-2 mb-4 border-bottom navbar-light'
      aria-label='navbar'
    >
      <div className='container'>
        <div
          onClick={() => navigate('/')}
          className='align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none cursor-pointer'
          role='button'
        >
          <img
            src={seqcol_logo}
            alt='Refget Sequence Collections'
            height='40'
          />
          <span className='ms-2'>Refget Sequence Collections</span>
        </div>

        <button
          className='navbar-toggler'
          type='button'
          data-bs-toggle='collapse'
          data-bs-target='#navbarSupportedContent'
          aria-controls='navbarSupportedContent'
          aria-expanded='false'
          aria-label='Toggle navigation'
        >
          <span className='navbar-toggler-icon'></span>
        </button>

        <div
          className='collapse navbar-collapse me-auto'
          id='navbarSupportedContent'
        >
          <ul className='navbar-nav ms-auto mb-2 mb-sm-0'>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/')}
                className={`nav-link cursor-pointer ${location === '' ? 'fw-medium text-black' : 'fw-light'}`}
              >
                Home
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/fasta')}
                className={`nav-link cursor-pointer ${location.startsWith('fasta') ? 'fw-medium text-black' : 'fw-light'}`}
              >
                FASTADigest
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/scim')}
                className={`nav-link cursor-pointer ${location.startsWith('scim') ? 'fw-medium text-black' : 'fw-light'}`}
              >
                SCIM
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/scom')}
                className={`nav-link cursor-pointer ${location.startsWith('scom') ? 'fw-medium text-black' : 'fw-light'}`}
              >
                SCOM
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/compliance')}
                className={`nav-link cursor-pointer ${location.startsWith('compliance') ? 'fw-medium text-black' : 'fw-light'}`}
              >
                Compliance
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <a
                href={`${API_BASE}/docs`}
                className='nav-link fw-light'
                target='_blank'
                rel='noopener noreferrer'
              >
                API
              </a>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <a
                href='https://github.com/refgenie/refget'
                className='nav-link fw-light'
                target='_blank'
                rel='noopener noreferrer'
              >
                GitHub
              </a>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <a
                href='https://ga4gh.github.io/refget/'
                className='nav-link fw-light'
                target='_blank'
                rel='noopener noreferrer'
              >
                Specification
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

class ReactErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ReactErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className='alert alert-danger' role='alert'>
          <strong>Something went wrong.</strong>
          <p className='mt-2'>{this.state.error?.message || 'An unexpected error occurred.'}</p>
          <button
            className='btn btn-danger mt-2'
            onClick={() => window.location.reload()}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const App = () => {
  const loaderData = useLoaderData();
  return (
    <>
      <Nav />
      <main className='container'>
        <ReactErrorBoundary>
          <Outlet />
        </ReactErrorBoundary>
      </main>
      <div className='container'>
        <footer className='flex-wrap py-3 my-4 align-top d-flex justify-content-between align-items-center border-top'>
          <div className='d-flex flex-column'>
            <div>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                refget {loaderData['version']['refget_version']}
              </span>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                gtars {loaderData['version']['gtars_version']}
              </span>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                python {loaderData['version']['python_version']}
              </span>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                seqcol spec {loaderData['version']['seqcol_spec_version']}
              </span>
            </div>
            <div className='d-flex flex-row mt-1 align-items-center'>
              <div className='p-1 bg-success border border-success rounded-circle me-1'></div>
              Connected
            </div>
          </div>
          <div className='ms-auto'>
            <a href='https://databio.org/'>
              <img
                src={databio_logo}
                alt='Sheffield Computational Biology Lab'
                width='200'
              />
            </a>
          </div>
        </footer>
      </div>
    </>
  );
};

function ErrorBoundary() {
  const error = useRouteError();
  console.error(error);

  const isNetworkError =
    error.message?.includes('Failed to fetch') ||
    error.message?.includes('NetworkError');
  const isNotFound = error.isNotFound || error.message?.includes('not found');

  const CopyableDigest = ({ digest }) => (
    <code
      className='user-select-all bg-light px-2 py-1 rounded cursor-pointer'
      style={{ fontSize: '0.85em' }}
      onClick={() => copyToClipboard(digest)}
      title='Click to copy'
    >
      {digest}
    </code>
  );

  return (
    <div className='alert alert-danger' role='alert'>
      <strong>Error:</strong> {error.message}
      <hr />
      {isNetworkError ? (
        <p>
          Could not connect to the API at{' '}
          <a href={`${API_BASE}`}>{API_BASE}</a>.
          <br />
          Make sure the server is running and accessible.
        </p>
      ) : isNotFound ? (
        <div>
          <p>
            The requested collection(s) do not exist on this server.
          </p>
          {error.digest1 && error.digest2 && (
            <div className='mb-3'>
              <div className='mb-2'>
                <strong>Digest A:</strong>{' '}
                <CopyableDigest digest={error.digest1} />
              </div>
              <div>
                <strong>Digest B:</strong>{' '}
                <CopyableDigest digest={error.digest2} />
              </div>
            </div>
          )}
          <p className='mb-0'>
            API: <a href={`${API_BASE}`}>{API_BASE}</a>
          </p>
        </div>
      ) : (
        <p>
          Is the API service operating correctly at{' '}
          <a href={`${API_BASE}`}>{API_BASE}</a>?
        </p>
      )}
      <button
        className='btn btn-danger mt-3'
        onClick={() => window.location.reload()}
      >
        Reload
      </button>
    </div>
  );
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    loader: fetchServiceInfo,
    errorElement: <ErrorBoundary />,
    children: [
      {
        path: '/',
        element: <HomePage />,
        errorElement: <ErrorBoundary />,
        loader: fetchSeqColList,
      },
      {
        path: '/demo',
        element: <DemoPage />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/fasta',
        element: <DigestPage />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/compliance',
        element: <CompliancePage />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/human',
        element: <HumanReferencesView />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/hprc',
        element: <HPRCGenomes />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/scim',
        element: <SCIM />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/scom',
        element: <SCOM />,
        errorElement: <ErrorBoundary />,
        loader: fetchAllSeqCols,
      },
      {
        path: '/scim/:digest1/:digest2',
        element: <SCIM />,
        errorElement: <ErrorBoundary />,
        loader: (request) => {
          return fetchComparison(
            request.params.digest1,
            request.params.digest2,
          );
        },
      },
      {
        path: '/collection/:digest',
        element: <CollectionView />,
        errorElement: <ErrorBoundary />,
        loader: (request) => {
          return fetchCollectionLevels(request.params.digest);
        },
      },
      {
        path: '/attribute/:attribute/:digest',
        element: <AttributeView />,
        errorElement: <ErrorBoundary />,
        loader: (request) => {
          return fetchAttribute(
            request.params.attribute,
            request.params.digest,
          );
        },
      },
      {
        path: '/pangenome/:digest',
        element: <PangenomeView />,
        errorElement: <ErrorBoundary />,
        loader: (request) => fetchPangenomeLevels(request.params.digest),
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Toaster position='top-right' />
    <RouterProvider router={router} />
  </React.StrictMode>,
);
