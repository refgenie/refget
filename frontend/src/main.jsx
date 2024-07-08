import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

import databio_logo from "./assets/logo_databio_long.svg"
import seqcol_logo from "./assets/seqcol_logo.svg"
import { useState } from 'react'

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { CollectionView } from './pages/CollectionView.jsx'
import { PangenomeView } from './pages/PangenomeView.jsx'
import { AttributeView } from './pages/AttributeView.jsx'
import { DemoPage } from './pages/DemoPage.jsx'
import { ComparisonView } from './pages/ComparisonView.jsx'


import { AttributeValue, LinkedAttributeDigest } from './components/ValuesAndDigests.jsx'
import { CollectionList, PangenomeList } from './components/ObjectLists.jsx'
import { copyToClipboardIcon, copyToClipboard } from "./utilities";

import {
  Outlet,
  Link,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useParams,
  useRouteError
} from "react-router-dom";


import { API_BASE } from './utilities.jsx'

const fetchPangenomeLevels = async(digest, level="2", collated=true) => {
  const url = `${API_BASE}/pangenome/${digest}?level=1`
  const url2 = `${API_BASE}/pangenome/${digest}?level=2`
  const urlItemwise = `${API_BASE}/pangenome/${digest}?collated=false`  
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json()),
    fetch(urlItemwise).then((response) => response.json())
  ]
  
  return Promise.all(resps)
}

const fetchSeqColList = async() => {
  const url = `${API_BASE}/list/collections?limit=10&offset=10`
  const url2 = `${API_BASE}/list/pangenomes?limit=5`
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json())
  ]
  return Promise.all(resps)
}

const fetchSeqColDetails = async(digest, level="2", collated=true) => {
  const url = `${API_BASE}/collection/${digest}?level=${level}&collated=${collated}`
  return fetch(url).then((response) => response.json())
}

const fetchCollectionLevels = async(digest) => {
  let url = `${API_BASE}/collection/${digest}?level=1`
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(`${API_BASE}/collection/${digest}?level=2`).then((response) => response.json()),
    fetch(`${API_BASE}/collection/${digest}?collated=false`).then((response) => response.json()) 
  ]
  return Promise.all(resps)
}


const fecthComparison = async(digest1, digest2) => {
  const url = `${API_BASE}/comparison/${digest1}/${digest2}`
  return fetch(url).then((response) => response.json())
}

const fetchAttribute = async(attribute, digest) => {
  const url = `${API_BASE}/attribute/${attribute}/${digest}/list`
  const url2 = `${API_BASE}/attribute/${attribute}/${digest}`
  let resps = [
    fetch(url).then((response) => response.json()),
    fetch(url2).then((response) => response.json())
  ]
  return Promise.all(resps)
}



const Level1Collection = ({collection}) => {
  return (
    <div>
      Names: <Link to={`/attribute/names/${collection.names}`}>{collection.names}</Link><br/>
      Lengths: <Link to={`/attribute/lengths/${collection.lengths}`}>{collection.lengths}</Link><br/>
      Sequences: <Link to={`/attribute/sequences/${collection.sequences}`}>{collection.sequences}</Link><br/>
    </div>
  )
}

const Level2Collection = ({collection}) => {
  return (
    <div>
      <h3>Names</h3>
      <pre>{JSON.stringify(collection.names, null, 2)}</pre>
      <h3>Lengths</h3>
      <pre>{JSON.stringify(collection.lengths, null, 2)}</pre>
      <h3>Sequences</h3>
      <pre>{JSON.stringify(collection.sequences, null, 2)}</pre>
    </div>
  )
}





const Nav = () => {
  return  (
    <nav className="navbar navbar-expand-lg py-2 mb-4 border-bottom navbar-light" aria-label="navbar">
      <div className="container">
        <a href="/" className="align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none">
        <img src={seqcol_logo} alt="Refget Sequence Collections" height="40"/> Refget Sequence Collections
        </a>
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse me-auto" id="navbarSupportedContent">
          <ul className="navbar-nav ms-auto mb-2 mb-sm-0">        
              <li className="nav-item mx-2 my-0 h5"><a href="/" className="nav-link">Home</a></li>
            
              <li className="nav-item mx-2 my-0 h5"><a href={`${API_BASE}/docs`} className="nav-link">API Docs</a></li>
            
              <li className="nav-item mx-2 my-0 h5"><a href="https://github.com/refgenie/refget" className="nav-link">GitHub</a></li>
            
              <li className="nav-item mx-2 my-0 h5"><a href="https://ga4gh.github.io/refget/" className="nav-link">Spec</a></li>
            
          </ul>
        </div>
      </div>
    </nav>
  )
}

const App = () => { 
  const refget_version = "0.5.0"
  return (<>
    <Nav/>
    <main className="container">
      <Outlet/>
    </main>
    <div className="container">
      <footer className="flex-wrap py-3 my-4 align-top d-flex justify-content-between align-items-center border-top">
        <div className="d-flex flex-column"><div>
          <span className="badge rounded-pill bg-primary text-primary bg-opacity-25 border border-primary me-1">refget {refget_version}</span>
          </div>
        <div className="d-flex flex-row mt-1 align-items-center">
          <div className="p-1 bg-success border border-success rounded-circle me-1"></div>
          Connected</div>
          </div><div className="ms-auto"><a href="https://databio.org/"><img src={databio_logo} alt="Sheffield Computational Biology Lab" width="200"/></a></div>
      </footer>
    </div>
    <ToastContainer />
  </>)
}





const CollectionTable = ({collections}) => {
  const seqColList = collections || useLoaderData()
  console.log("seqColList", seqColList)
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
    {seqColList["items"].map((collection) => (
      <tr key={collection}>
        <td><LinkedCollectionDigest digest={collection.digest} clipboard={false}/></td>
        <td className="tiny mx-2"><LinkedAttributeDigest attribute="names" digest={collection.names_digest} clipboard={false}/></td>
        <td className="tiny mx-2"><LinkedAttributeDigest attribute="lengths" digest={collection.lengths_digest} clipboard={false} /></td>
        <td className="tiny mx-2"><LinkedAttributeDigest attribute="sequences" digest={collection.sequences_digest} clipboard={false} /></td>
      </tr>
    ))}
    </tbody>
  </table>
  )
}


const HomePage = () => {
  const loaderData = useLoaderData()
  console.log("HomePage loadData ", loaderData)
  const collections = loaderData[0]
  const pangenomes = loaderData[1]

  const PangenomeExamplesList = () => {
    if (pangenomes.items[0]) {
      return <>
        <h3>Example Pangenomes:</h3>
        <PangenomeList pangenomes={pangenomes}/>
      </>
    } else {
      return ""
    } 
  }

  return (
    <div>
      <p>Welcome to the Refget Sequence Collections demo service!
        This landing page provides a way to explore the data in the server.
        You can go straight to the API itself using the <b>API Docs</b> link in the title bar.
        Or, you can check out a few examples below. Here are two easy ways to browse:
      </p>

      <h5>1. View and compare the demo sequence collections:</h5>
      <p className="text-muted fs-6">
        This service includes several small demo collections. This page will show you 
        comparisons between them:
      </p>

      <ul>
        <li><Link to="/demo">Demo of collection comparisons</Link></li>
      </ul>
      
      <h5 className="mt-4">2. Example Sequence Collections from the human pangenome reference consortium available on this server:</h5>
      <p className="text-muted fs-6">
        This uses the <span className="font-monospace text-success">/list/collections</span> endpoint,
        which provides a paged list of all collections hosted by this server.
      </p>

      <CollectionList collections={collections}/>
      <PangenomeExamplesList/>
    </div>
  )
//       <CompareTable seqColList={collections.items}/>
}

function ErrorBoundary() {
  const error = useRouteError();
  console.error(error);
  return <div class="alert alert-danger" role="alert">
    {error.message}
    Is the API service operating correctly at <a href={`${API_BASE}`}>{API_BASE}</a>?<br/>
    <button className="btn btn-danger" onClick={() => window.location.reload()}>Reload</button>
  </div>;
}



const router = createBrowserRouter([
  {
    path: "/",
    element: <App/>,
    children: [
      {
        path: "/",
        element: <HomePage/>,
        errorElement: <ErrorBoundary />,
        loader: fetchSeqColList
      }, 
      { 
        path: "/demo",
        element: <DemoPage/>
      },
      {
        path: "/comparison/:digest1/:digest2",
        element: <ComparisonView/>,
        loader: (request) => {
          console.log("params", request.params)
          return fecthComparison(request.params.digest1, request.params.digest2)
        }
      },
      {
        path: "/collection/:digest",
        element: <CollectionView/>,
        loader: (request) => {
          console.log("params", request.params)
          return fetchCollectionLevels(request.params.digest)
        }
      },
      {
        path: "/attribute/:attribute/:digest",
        element: <AttributeView/>,
        loader: (request) =>{ 
          console.log("params", request.params)
          return fetchAttribute(request.params.attribute, request.params.digest)
        
        }
      },
      {
        path: "/pangenome/:digest",
        element: <PangenomeView/>,
        loader: (request) => fetchPangenomeLevels(request.params.digest)
      }
    ]
  },
]);


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
