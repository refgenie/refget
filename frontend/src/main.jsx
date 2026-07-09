// This is the application entry/router module: it intentionally co-locates the
// route component definitions (Nav, App, ErrorBoundary, ...) with the router and
// loader setup. It is the render root, not a hot-reloaded component module, so
// the Fast Refresh "only export components" rule does not meaningfully apply.
/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';

import './index.css';

import databio_logo from './assets/logo_databio_long.svg';
import seqcol_logo from './assets/seqcol_logo.svg';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/js/bootstrap.bundle.js';
import 'bootstrap-icons/font/bootstrap-icons.css';

// Unified Explorer pages
import { LandingPage } from './pages/LandingPage.jsx';
import { ExplorePage } from './pages/ExplorePage.jsx';
import { Explorer } from './pages/Explorer.jsx';
import { ExplorerCollection } from './pages/ExplorerCollection.jsx';
import { ExplorerSequences } from './pages/ExplorerSequences.jsx';
import { ExplorerAliases } from './pages/ExplorerAliases.jsx';

// API Explorer pages
import { APIExplorer } from './pages/APIExplorer.jsx';
import { APICollections } from './pages/APICollections.jsx';
import { APICollectionView } from './pages/APICollectionView.jsx';
import { APICompare } from './pages/APICompare.jsx';

// Store Explorer pages
import { StoreExplorer } from './pages/StoreExplorer.jsx';
import { StoreOverview } from './pages/StoreOverview.jsx';
import { StoreSequences } from './pages/StoreSequences.jsx';
import { StoreCollection } from './pages/StoreCollection.jsx';
import { StoreAliases } from './pages/StoreAliases.jsx';

// Site-specific pages
import { PangenomeView } from './pages/PangenomeView.jsx';
import { AttributeView } from './pages/AttributeView.jsx';
import { SCIM } from './pages/SCIM.jsx';
import { SCOM } from './pages/SCOM.jsx';
import { HumanReferencesView } from './pages/HumanReferences.jsx';
import { DigestPage } from './pages/DigestPage.jsx';
import { VrsConverter } from './pages/VrsConverter.jsx';
import { CompliancePage } from './pages/CompliancePage.jsx';
import { JungleBrowser } from './pages/JungleBrowser.jsx';

import {
  fetchServiceInfo,
  fetchPangenomeLevels,
  fetchAllSeqCols,
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

const NavItem = ({ path, label, location, navigate, isDropdown }) => {
  const active = path === '/'
    ? location === ''
    : location.startsWith(path.substring(1));

  return (
    <li className={`nav-item mx-2 my-0 h6 ${isDropdown ? '' : ''}`}>
      <span
        onClick={() => navigate(path)}
        className={`nav-link cursor-pointer ${active ? 'fw-medium text-black' : 'fw-light'}`}
      >
        {label}
      </span>
    </li>
  );
};

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
            <NavItem path="/" label="Home" location={location} navigate={navigate} />

            {/* The Specification - external link */}
            <li className='nav-item mx-2 my-0 h6'>
              <a
                href='https://ga4gh.github.io/refget/'
                className='nav-link fw-light'
                target='_blank'
                rel='noopener noreferrer'
              >
                Specification <i className='bi bi-box-arrow-up-right' style={{ fontSize: '0.7em' }}></i>
              </a>
            </li>

            {/* Python Package - external link */}
            <li className='nav-item mx-2 my-0 h6'>
              <a
                href='https://refgenie.org/refget/'
                className='nav-link fw-light'
                target='_blank'
                rel='noopener noreferrer'
              >
                Python <i className='bi bi-box-arrow-up-right' style={{ fontSize: '0.7em' }}></i>
              </a>
            </li>

            {/* Explore link */}
            <NavItem path="/explore" label="Explore" location={location} navigate={navigate} />

            {/* VRS converter */}
            <NavItem path="/vrs" label="VRS" location={location} navigate={navigate} />

            {/* GitHub dropdown */}
            <li className='nav-item dropdown mx-2 my-0 h6'>
              <span
                className='nav-link cursor-pointer dropdown-toggle fw-light'
                role='button'
                data-bs-toggle='dropdown'
                aria-expanded='false'
              >
                GitHub
              </span>
              <ul className='dropdown-menu dropdown-menu-end'>
                <li>
                  <a
                    href='https://github.com/ga4gh/refget'
                    className='dropdown-item'
                    target='_blank'
                    rel='noopener noreferrer'
                  >
                    <i className='bi bi-file-text me-2'></i>Specification
                  </a>
                </li>
                <li>
                  <a
                    href='https://github.com/refgenie/refget'
                    className='dropdown-item'
                    target='_blank'
                    rel='noopener noreferrer'
                  >
                    <i className='bi bi-code-slash me-2'></i>Python Package
                  </a>
                </li>
              </ul>
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
  const apiAvailable = loaderData != null;
  const version = loaderData?.version;

  return (
    <>
      <Nav />
      <main className='container'>
        <ReactErrorBoundary>
          <Outlet context={{ apiAvailable, serviceInfo: loaderData }} />
        </ReactErrorBoundary>
      </main>
      <div className='container'>
        <footer className='flex-wrap py-3 my-4 align-top d-flex justify-content-between align-items-center border-top'>
          <div className='d-flex flex-column'>
            {version ? (
              <>
                <div>
                  <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                    refget {version.refget_version}
                  </span>
                  <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                    gtars {version.gtars_version}
                  </span>
                  <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                    python {version.python_version}
                  </span>
                  <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                    seqcol spec {version.seqcol_spec_version}
                  </span>
                </div>
                <div className='d-flex flex-row mt-1 align-items-center'>
                  <div className='p-1 bg-success border border-success rounded-circle me-1'></div>
                  Connected to {API_BASE}
                </div>
              </>
            ) : (
              <div className='d-flex flex-row mt-1 align-items-center'>
                <div className='p-1 bg-warning border border-warning rounded-circle me-1'></div>
                <span className='text-muted'>API unavailable</span>
              </div>
            )}
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

  // Plain render helper (not a component) so it isn't re-created as a new
  // component type on every render.
  const renderCopyableDigest = (digest) => (
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
                {renderCopyableDigest(error.digest1)}
              </div>
              <div>
                <strong>Digest B:</strong>{' '}
                {renderCopyableDigest(error.digest2)}
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
      // Landing page
      {
        path: '/',
        element: <LandingPage />,
        errorElement: <ErrorBoundary />,
      },

      // Explore page (4-card disambiguation)
      {
        path: '/explore',
        element: <ExplorePage />,
        errorElement: <ErrorBoundary />,
      },

      // Unified Explorer
      {
        path: '/collections',
        element: <Explorer />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/collection/:digest',
        element: <ExplorerCollection />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/sequences',
        element: <ExplorerSequences />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/aliases',
        element: <ExplorerAliases />,
        errorElement: <ErrorBoundary />,
      },

      // Shared tools (standalone)
      {
        path: '/fasta',
        element: <DigestPage />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/vrs',
        element: <VrsConverter />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/compare',
        element: <SCIM />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/compare/:digest1/:digest2',
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
        path: '/compliance',
        element: <CompliancePage />,
        errorElement: <ErrorBoundary />,
      },

      // Site-specific curated pages
      {
        path: '/jungle',
        element: <JungleBrowser />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/scom',
        element: <SCOM />,
        errorElement: <ErrorBoundary />,
        loader: () => fetchAllSeqCols(),
      },
      {
        path: '/human',
        element: <HumanReferencesView />,
        errorElement: <ErrorBoundary />,
      },

      // Attribute view (linked from explorer)
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

      // Store Explorer (generic tool)
      {
        path: '/explore-store',
        element: <StoreExplorer />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/overview',
        element: <StoreOverview />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/sequences',
        element: <StoreSequences />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/collection/:digest',
        element: <StoreCollection />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/aliases',
        element: <StoreAliases />,
        errorElement: <ErrorBoundary />,
      },

      // API Explorer (generic tool)
      {
        path: '/explore-api',
        element: <APIExplorer />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-api/collections',
        element: <APICollections />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-api/collection/:digest',
        element: <APICollectionView />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-api/compare',
        element: <APICompare />,
        errorElement: <ErrorBoundary />,
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
