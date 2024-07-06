import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

import compare from './assets/compare.svg'
import { useState } from 'react'

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { CollectionView } from './pages/CollectionView.jsx'
import { PangenomeView } from './pages/PangenomeView.jsx'
import { AttributeView } from './pages/AttributeView.jsx'
import { AttributeValue, LinkedAttributeDigest } from './components/Attributes.jsx'
import { CollectionList, PangenomeList } from './components/ObjectLists.jsx'


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
  const url = `${API_BASE}/list/collections?limit=20`
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
    fetch(`${API_BASE}/collection/${digest}?level=2`).then((response) => response.json()) 
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

const LinkedCollectionDigest = ({digest, clipboard=true}) => {
  return (<>
    <Link to={`/collection/${digest}`} className="font-monospace">{digest}</Link> 
    { clipboard ? <img src={copyToClipboardIcon} alt="Copy" width="30" className="copy-to-clipboard mx-2" onClick={ () => navigator.clipboard.writeText(digest)}/> : "" }
    </>
  )
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



const ComparisonView =() => { 
  const comparison = useLoaderData()
  console.log("ComparisonView", comparison)
  const comp_str = JSON.stringify(comparison, null, 2)
  
  let api_url = `${API_BASE}/comparison/${comparison.digests.a}/${comparison.digests.b}`

  return (
    <div>
      <h1>Comparison</h1>
      <div>
        API URL: <Link to={api_url}>{api_url}</Link><br/>
        <label className="col-sm-4 fw-bold">Digest A:</label>
        <LinkedCollectionDigest digest={comparison.digests.a}/>
        </div>
      <div>
        <label className="col-sm-4 fw-bold">Digest B:</label>
        <LinkedCollectionDigest digest={comparison.digests.b}/>
      </div>
      <h3>Attributes</h3>
      <div className="row mb-3">
      <label className="col-sm-4 fw-bold">Found in collection A only:</label>
      {comparison.attributes.a_only.join(', ')}
      </div>
      <div className="row mb-3">
      <label className="col-sm-4 fw-bold">Found in both:</label>
      {comparison.attributes.a_and_b.join(', ')}
      </div>
      

      <h3>Array Elements</h3>
      <div className="row mb-3">
      <label className="col-sm-4 fw-bold">Found in both:</label>
      {Object.entries(comparison.array_elements.a_and_b).map(([key, value]) => (
        <div className="row mb-3">
          <label className="col-sm-4 fw-bold">{key}</label>{value}
        </div>
      ))}
      </div>
      {comp_str}
    </div>
  )

}

const CompareTable = ({seqColList}) => {  

  function buildCompareLinks(seqColList) {
    let header_cells = [];
    for (let i = 0; i < seqColList.length; i++) {
      header_cells.push(<th key={"header_col_"+i} className='rotated-text'><div>{seqColList[i]}</div></th>)
    }
    let header_row = <tr><th></th>{header_cells}</tr>;

    let link_rows = [];
    for (let i = 0; i < seqColList.length; i++) {
      let link_cells = []
      link_cells.push(<th className="text-end" key={"header_row_"+i}><Link to={`/collection/${seqColList[i]}`}>{seqColList[i]}</Link></th>)
      for (let j = 0; j < seqColList.length; j++) {
        link_cells.push(
          <td key={i + "vs" + j} className="text-center">{ j == i ? "=" : <Link
            to={`/comparison/${seqColList[i]}/${seqColList[j]}`}
            key={`${seqColList[i]}-${seqColList[j]}`}
          ><img src={compare} alt="Compare" width="50" className="compare"/>
          </Link>}</td>
        );
      }
      link_rows.push(<tr key={"row_" + i}>{link_cells}</tr>);
    }
    let table = <table border="0">
      <thead>{header_row}</thead>
      <tbody>{link_rows}</tbody>
    </table>;
    return table;
  }

  return  <>     
    <h1>Comparison table</h1>
    {buildCompareLinks(seqColList)}
  </>
}



const Nav = () => {
  return  (
    <nav className="navbar navbar-expand-lg py-2 mb-4 border-bottom navbar-light" aria-label="navbar">
      <div className="container">
        <a href="/" className="align-items-center mb-3 mb-md-0 me-md-auto text-dark text-decoration-none">
        Refget Sequence Collections
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
  return (<>
    <Nav/>
    <div className="container">
      <Outlet/>
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
      <h2>Welcome</h2>
      <p>Welcome to the Refget Sequence Collections service!
        This landing page provides a way to explore the data in the server.
        You can go straight to the API itself using the <b>API Docs</b> link in the title bar.
        Or, you can check out a few examples below
      </p>

      <PangenomeExamplesList/>
      
      <h3>Example Sequence Collections</h3>
      <p>Here are some available sequence collections:</p>
      <CollectionList collections={collections}/>

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
