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
import { Similarities } from './pages/Similarities.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { HPRCGenomes } from './pages/HPRCGenomes.jsx';
import { HumanReferencesView } from './pages/HumanReferences.jsx';

import {
  fetchServiceInfo,
  fetchPangenomeLevels,
  fetchSeqColList,
  fetchAllSeqCols,
  fetchCollectionLevels,
  fetchComparison,
  fetchAttribute,
} from './services/fetchData.jsx';

import {
  AttributeValue,
  LinkedAttributeDigest,
} from './components/ValuesAndDigests.jsx';
import { CollectionList, PangenomeList } from './components/ObjectLists.jsx';
import { copyToClipboardIcon, copyToClipboard } from './utilities';

import {
  Outlet,
  Link,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useParams,
  useRouteError,
  useNavigate,
  useLocation,
} from 'react-router-dom';

import { API_BASE } from './utilities.jsx';

const Level1Collection = ({ collection }) => {
  return (
    <div>
      Names:{' '}
      <Link to={`/attribute/collection/names/${collection.names}`}>
        {collection.names}
      </Link>
      <br />
      Lengths:{' '}
      <Link to={`/attribute/collection/lengths/${collection.lengths}`}>
        {collection.lengths}
      </Link>
      <br />
      Sequences:{' '}
      <Link to={`/attribute/collection/sequences/${collection.sequences}`}>
        {collection.sequences}
      </Link>
      <br />
    </div>
  );
};

const Level2Collection = ({ collection }) => {
  return (
    <div>
      <h3>Names</h3>
      <pre>{JSON.stringify(collection.names, null, 2)}</pre>
      <h3>Lengths</h3>
      <pre>{JSON.stringify(collection.lengths, null, 2)}</pre>
      <h3>Sequences</h3>
      <pre>{JSON.stringify(collection.sequences, null, 2)}</pre>
    </div>
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
                onClick={() => navigate('/scim')}
                className={`nav-link cursor-pointer ${location === 'scim' ? 'fw-medium text-black' : 'fw-light'}`}
              >
                SCIM
              </span>
            </li>
            <li className='nav-item mx-2 my-0 h6'>
              <span
                onClick={() => navigate('/similarities')}
                className={`nav-link cursor-pointer ${location === 'similarities' ? 'fw-medium text-black' : 'fw-light'}`}
              >
                Similarities
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

const App = () => {
  const loaderData = useLoaderData();
  const refgetVersion = loaderData['version']['refget_pkg_version'];
  return (
    <>
      <Nav />
      <main className='container'>
        <Outlet />
      </main>
      <div className='container'>
        <footer className='flex-wrap py-3 my-4 align-top d-flex justify-content-between align-items-center border-top'>
          <div className='d-flex flex-column'>
            <div>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                refget {refgetVersion}
              </span>
              <span className='badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1'>
                seqcolapi {loaderData['version']['seqcolapi_version']}
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

const CollectionTable = ({ collections }) => {
  const seqColList = collections || useLoaderData();
  return (
    <table>
      <thead>
        <tr>
          <th>Collection digest</th>
          <th>Names</th>
          <th>Lengths</th>
          <th>Sequences</th>
        </tr>
      </thead>
      <tbody>
        {seqColList['results'].map((collection) => (
          <tr key={collection}>
            <td>
              <LinkedCollectionDigest
                digest={collection.digest}
                clipboard={false}
              />
            </td>
            <td className='tiny mx-2'>
              <LinkedAttributeDigest
                attribute='names'
                digest={collection.names_digest}
                clipboard={false}
              />
            </td>
            <td className='tiny mx-2'>
              <LinkedAttributeDigest
                attribute='lengths'
                digest={collection.lengths_digest}
                clipboard={false}
              />
            </td>
            <td className='tiny mx-2'>
              <LinkedAttributeDigest
                attribute='sequences'
                digest={collection.sequences_digest}
                clipboard={false}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

function ErrorBoundary() {
  const error = useRouteError();
  console.error(error);
  return (
    <div className='alert alert-danger' role='alert'>
      {error.message}
      <br></br>
      Is the API service operating correctly at{' '}
      <a href={`${API_BASE}`}>{API_BASE}</a>?<br />
      <button
        className='btn btn-danger'
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
      },
      {
        path: '/human',
        element: <HumanReferencesView />,
      },
      {
        path: '/hprc',
        element: <HPRCGenomes />,
      },
      {
        path: '/scim',
        element: <SCIM />,
      },
      {
        path: '/similarities',
        element: <Similarities />,
        loader: fetchAllSeqCols,
      },
      {
        path: '/scim/:digest1/:digest2',
        element: <SCIM />,
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
