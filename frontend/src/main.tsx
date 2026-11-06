// This is the application entry/router module: it intentionally co-locates the
// route component definitions (Nav, App, ErrorBoundary, ...) with the router and
// loader setup. It is the render root, not a hot-reloaded component module, so
// the Fast Refresh "only export components" rule does not meaningfully apply.
/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { useState } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';

import './styles/main.css';

import databio_logo from './assets/logo_databio_long.svg';
import seqcol_logo from './assets/seqcol_logo.svg';

// Unified Explorer pages
import { LandingPage } from './pages/LandingPage';
import { ExplorePage } from './pages/ExplorePage';
import { LegacyRedirect } from './pages/LegacyRedirect';

// API Explorer pages
import { APIExplorer } from './pages/APIExplorer';
import { APICollections } from './pages/APICollections';
import { APICollectionView } from './pages/APICollectionView';
import { APICompare } from './pages/APICompare';

// Store Explorer pages
import { StoreExplorer } from './pages/StoreExplorer';
import { StoreOverview } from './pages/StoreOverview';
import { StoreSequences } from './pages/StoreSequences';
import { StoreCollection } from './pages/StoreCollection';
import { StoreAliases } from './pages/StoreAliases';
import { StorePage } from './components/StorePage';

// Site-specific pages
import { PangenomeView } from './pages/PangenomeView';
import { AttributeView } from './pages/AttributeView';
import { SCIM } from './pages/SCIM';
import { SCOM } from './pages/SCOM';
import { HumanReferencesView } from './pages/HumanReferences';
import { DigestPage } from './pages/DigestPage';
import { VrsConverter } from './pages/VrsConverter';
import { CompliancePage } from './pages/CompliancePage';
import { JungleBrowser } from './pages/JungleBrowser';

import {
  fetchServiceInfo,
  fetchPangenomeLevels,
  fetchAllSeqCols,
  fetchComparison,
  fetchAttribute,
} from './services/fetchData';

import { copyToClipboard } from './utilities';
import { cn } from './utils/cn';
import type { AppError, ServiceInfo } from './types';

import {
  Link,
  Outlet,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useRouteError,
  useLocation,
} from 'react-router-dom';
import type { LoaderFunctionArgs } from 'react-router-dom';

import { API_BASE } from './utilities';
import storeList from './data/stores.json';

// The store this site's API serves, for the footer ("the Jungle API").
const apiStore = storeList.find((s) => 'api' in s && s.api === API_BASE);
import { Icon } from './components/common/Icon';

interface NavItemProps {
  path: string;
  label: string;
  location: string;
}

const NavItem = ({ path, label, location }: NavItemProps) => {
  const active = path === '/'
    ? location === ''
    : location.startsWith(path.substring(1));

  return (
    <li>
      <Link
        to={path}
        className={cn('site-nav__link', active && 'site-nav__link--active')}
        aria-current={active ? 'page' : undefined}
      >
        {label}
      </Link>
    </li>
  );
};

const Nav = () => {
  const location = useLocation().pathname.substring(1) || '';
  // Bootstrap's collapse plugin is gone; the mobile menu is React state now.
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className='site-nav' aria-label='navbar'>
      <div className='site-nav__inner'>
        <Link to='/' className='site-nav__brand'>
          <img
            src={seqcol_logo}
            alt='Refget Sequence Collections'
            className='site-nav__logo'
          />
          <span>Refget Sequence Collections</span>
        </Link>

        <button
          type='button'
          className='site-nav__link ml-auto md:hidden'
          aria-expanded={menuOpen}
          aria-label='Toggle navigation'
          onClick={() => setMenuOpen((open) => !open)}
        >
          <Icon name='three-dots' className='icon--lg' />
        </button>

        <ul className={cn('site-nav__list', menuOpen ? 'flex' : 'hidden', 'md:flex')}>
          <NavItem path='/' label='Home' location={location} />

          {/* The Specification - external link */}
          <li>
            <a
              href='https://ga4gh.github.io/refget/'
              className='site-nav__link'
              target='_blank'
              rel='noopener noreferrer'
            >
              Specification <Icon name='external' />
            </a>
          </li>

          {/* Python Package - external link */}
          <li>
            <a
              href='https://docs.refgenie.org/refget/'
              className='site-nav__link'
              target='_blank'
              rel='noopener noreferrer'
            >
              Python <Icon name='external' />
            </a>
          </li>

          {/* Explore link */}
          <NavItem path='/explore' label='Explore' location={location} />

          {/* VRS converter */}
          <NavItem path='/vrs' label='VRS' location={location} />

          {/* This site's source code; the spec and docs links above cover the rest */}
          <li>
            <a
              href='https://github.com/refgenie/refget'
              className='site-nav__link'
              target='_blank'
              rel='noopener noreferrer'
            >
              GitHub <Icon name='external' />
            </a>
          </li>
        </ul>
      </div>
    </nav>
  );
};

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ReactErrorBoundary extends React.Component<
  { children: ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ReactErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className='alert alert--danger' role='alert'>
          <strong>Something went wrong.</strong>
          <p className='mt-2'>{this.state.error?.message || 'An unexpected error occurred.'}</p>
          <button
            className='btn btn--danger mt-2'
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
  const loaderData = useLoaderData() as ServiceInfo | null;
  const apiAvailable = loaderData != null;
  const version = loaderData?.version;

  return (
    <>
      <Nav />
      <main className='page-main'>
        <ReactErrorBoundary>
          <Outlet context={{ apiAvailable, serviceInfo: loaderData }} />
        </ReactErrorBoundary>
      </main>
      <footer className='site-footer'>
        <div className='flex flex-col'>
          {version ? (
            <>
              <div className='flex flex-wrap gap-1'>
                <span className='badge badge--pill badge--primary'>
                  refget {version.refget_version}
                </span>
                <span className='badge badge--pill badge--primary'>
                  gtars {version.gtars_version}
                </span>
                <span className='badge badge--pill badge--primary'>
                  python {version.python_version}
                </span>
                <span className='badge badge--pill badge--primary'>
                  seqcol spec {version.seqcol_spec_version}
                </span>
              </div>
              <div className='flex flex-row mt-1 items-center gap-1'>
                <span className='dot dot--ok' />
                {apiStore
                  ? `Connected to the ${apiStore.name} API (${API_BASE.replace(/^https?:\/\//, '')})`
                  : `Connected to ${API_BASE}`}
              </div>
            </>
          ) : (
            <div className='flex flex-row mt-1 items-center gap-1'>
              <span className='dot dot--warn' />
              <span className='text-muted'>API unavailable</span>
            </div>
          )}
        </div>
        <a href='https://databio.org/'>
          <img
            src={databio_logo}
            alt='Sheffield Computational Biology Lab'
            className='site-footer__logo'
          />
        </a>
      </footer>
    </>
  );
};

function NotFound() {
  const { pathname } = useLocation();

  return (
    <div className='py-6'>
      <h2 className='text-2xl font-light mb-2'>Page not found</h2>
      <p className='text-muted'>
        There is no page at <code className='code code--inline'>{pathname}</code>.
      </p>
      <p className='text-muted text-sm mb-6'>
        The address may be mistyped or out of date. This is a problem with the
        link, not with the API.
      </p>
      <Link to='/' className='btn btn--primary mr-2'>
        <Icon name='house' />
        Home
      </Link>
      <Link to='/explore' className='btn btn--outline-primary'>
        <Icon name='compass' />
        Explore
      </Link>
    </div>
  );
}

function ErrorBoundary() {
  const error = useRouteError() as AppError | undefined;
  console.error(error);

  // Router ErrorResponses (thrown by a loader) carry status/statusText rather
  // than message, so falling back to message alone renders a blank error.
  const status = error?.status;
  const message =
    error?.message ||
    (status ? `${status} ${error?.statusText || ''}`.trim() : '') ||
    'An unexpected error occurred.';

  const isNetworkError =
    error?.message?.includes('Failed to fetch') ||
    error?.message?.includes('NetworkError');
  const isNotFound =
    error?.isNotFound || error?.message?.includes('not found') || status === 404;

  // Plain render helper (not a component) so it isn't re-created as a new
  // component type on every render.
  const renderCopyableDigest = (digest: string) => (
    <code
      className='digest'
      onClick={() => copyToClipboard(digest)}
      title='Click to copy'
    >
      {digest}
    </code>
  );

  return (
    <div className='alert alert--danger' role='alert'>
      <strong>Error:</strong> {message}
      <hr />
      {isNetworkError ? (
        <p>
          Could not connect to the API at <code className='code code--inline'>{API_BASE}</code>.
          <br />
          Make sure the server is running and accessible —{' '}
          <a href={`${API_BASE}/service-info`} target='_blank' rel='noopener noreferrer'>
            check its service-info
          </a>
          .
        </p>
      ) : isNotFound ? (
        <div>
          <p>
            The requested collection(s) do not exist on this server.
          </p>
          {error?.digest1 && error?.digest2 && (
            <div className='mb-4'>
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
            API: <code className='code code--inline'>{API_BASE}</code>
          </p>
        </div>
      ) : (
        <p>
          Is the API service operating correctly at <code className='code code--inline'>{API_BASE}</code>?{' '}
          <a href={`${API_BASE}/service-info`} target='_blank' rel='noopener noreferrer'>
            Check its service-info
          </a>
          .
        </p>
      )}
      <button
        className='btn btn--danger mt-4'
        onClick={() => window.location.reload()}
      >
        Reload
      </button>
    </div>
  );
}

/**
 * Route params are typed `string | undefined` even where the path segment is
 * required. A missing one means the route table and the loader disagree, which
 * is a bug, not a 404 -- so fail loudly rather than fetching "undefined".
 */
function requireParam(value: string | undefined, name: string): string {
  if (!value) throw new Error(`Route is missing the :${name} parameter`);
  return value;
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

      // Old explorer addresses, forwarded to the Store Explorer
      { path: '/collections', element: <LegacyRedirect page="collections" /> },
      { path: '/collection/:digest', element: <LegacyRedirect page="collection" /> },
      { path: '/sequences', element: <LegacyRedirect page="sequences" /> },
      { path: '/aliases', element: <LegacyRedirect page="aliases" /> },

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
        loader: ({ params }: LoaderFunctionArgs) => {
          return fetchComparison(
            requireParam(params.digest1, 'digest1'),
            requireParam(params.digest2, 'digest2'),
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
        // ?url= names the API the API Explorer is browsing; default API_BASE.
        loader: ({ params, request }: LoaderFunctionArgs) => {
          return fetchAttribute(
            requireParam(params.attribute, 'attribute'),
            requireParam(params.digest, 'digest'),
            new URL(request.url).searchParams.get('url'),
          );
        },
      },
      {
        path: '/pangenome/:digest',
        element: <PangenomeView />,
        errorElement: <ErrorBoundary />,
        loader: ({ params }: LoaderFunctionArgs) =>
          fetchPangenomeLevels(requireParam(params.digest, 'digest')),
      },

      // Store Explorer (generic tool)
      {
        path: '/explore-store',
        element: <StoreExplorer />,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/overview',
        element: <StorePage><StoreOverview /></StorePage>,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/sequences',
        element: <StorePage><StoreSequences /></StorePage>,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/collection/:digest',
        element: <StorePage><StoreCollection /></StorePage>,
        errorElement: <ErrorBoundary />,
      },
      {
        path: '/explore-store/aliases',
        element: <StorePage><StoreAliases /></StorePage>,
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

      // Catch-all. As a child route this renders inside <App/>, so an unknown
      // URL keeps the nav and footer instead of short-circuiting to the root
      // errorElement, which drops both and blames the API.
      {
        path: '*',
        element: <NotFound />,
        errorElement: <ErrorBoundary />,
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Toaster position='top-right' />
    <RouterProvider router={router} />
  </React.StrictMode>,
);
