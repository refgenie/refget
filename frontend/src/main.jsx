import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

import compare from './assets/compare.svg'
import copyToClipboardIcon from './assets/copy_to_clipboard.svg'
import { useState } from 'react'

import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


import {
  Outlet,
  Link,
  createBrowserRouter,
  RouterProvider,
  useLoaderData,
  useParams
} from "react-router-dom";

const API_BASE = "http://127.0.0.1:8100"

const fetchSeqColList = async() => {
  const url = `${API_BASE}/list`
  return fetch(url).then((response) => response.json())
}

const fetchSeqColDetails = async(digest, level="2", collated=true) => {
  const url = `${API_BASE}/collection/${digest}?level=${level}&collated=${collated}`
  return fetch(url).then((response) => response.json())
}

const fetchAllCol = async(digest) => {
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
  return fetch(url).then((response) => response.json())
}

const CollectionView = (params) => {
  const collection = useLoaderData()
  const [collectionRepresentation, setCollectionRepresentation] = useState(null)
  const { digest } = useParams()
  console.log("CollectionView", collection)
  
  let level1 = collection[0]
  let level2 = collection[1]

  console.log("Lev 1", level1)

  // const col_str = (2 == 1 ? "asdf" : <pre>{JSON.stringify(collectionRepresentation, null, 2)}</pre>)
  const showLevel = (level, collated=true) => { 
    console.log(`showing level ${level}`)
    fetchSeqColDetails(digest, level, collated).then((data) => {
      console.log("got data", data)
      if (level == 1) {
        data = Level1Collection(data)
      }
      else if (level == 2) {
        data = Level2Collection(data)
      }
      setCollectionRepresentation(data)
    })
  
    const showUncollated = () => {
      console.log("showing uncollated")
      fetchSeqColDetails(digest, "uncollated").then((data) => {
        console.log("got data", data)
        setCollectionRepresentation(data)
      })
    }

  }
  const api_url_level2 = `${API_BASE}/collection/${digest}`
  const api_url_level1 = `${API_BASE}/collection/${digest}?level=1`
  const api_url_uncollated = `${API_BASE}/collection/${digest}?collated=false`

  let attribute_list_views = []
  for ( let attribute in level2) {
    attribute_list_views.push(<>
    <h5 className="mb-2 mt-3">{attribute}</h5>
    <div className="row align-items-center">
      <div className="col-md-1 ">Digest:</div>
      <div className="col">
        <LinkedAttributeDigest attribute={attribute} digest={level1[attribute]}/>
      </div>
    </div>
    <div className="row align-items-center">
      <div className="col-md-1 ">Value:</div>
      <div className="col">
        <AttributeValue value={level2[attribute]} />
      </div>
    </div>
      </>
    )
  }

  return (
    <div>
      <h2>Sequence Collection: {digest}</h2>
      <ul>
        <h4>API URLs</h4>
        <li>Level 1: <Link to={api_url_level1}>{api_url_level1}</Link></li>
        <li>Level 2: <Link to={api_url_level2}>{api_url_level2}</Link></li>
        <li>Uncollated: <Link to={api_url_uncollated}>{api_url_uncollated}</Link></li>
      </ul>
      {attribute_list_views}
    </div>
  )
}


const LinkedCollectionDigest = ({digest, clipboard=true}) => {
  return (<>
    <Link to={`/collection/${digest}`} className="font-monospace">{digest}</Link> 
    { clipboard ? <img src={copyToClipboardIcon} alt="Copy" width="30" className="copy-to-clipboard mx-2" onClick={ () => navigator.clipboard.writeText(digest)}/> : "" }
    </>
  )
}

const AttributeValue = ({value}) => {
  return(<pre className="text-secondary m-0 p-2 border border-muted"><code>{value.join(",")}</code></pre>)
}

const AttributeView = () => { 
  const content = useLoaderData()
  const { attribute, digest } = useParams()
  const api_url = `${API_BASE}/attribute/${attribute}/${digest}`
  const api_url_list = `${API_BASE}/attribute/${attribute}/${digest}/list`

  return (
    <div>
      <h1>Attribute: {attribute} 
      </h1>
      <div className="row align-items-center">
        <div className="col-md-1">API URL:</div>
        <div className="col"><Link to={api_url}>{api_url}</Link></div>
      </div>
      <div className="row align-items-center">
        <div className="col-md-1">Digest:</div>
        <div className="col">
          <LinkedAttributeDigest attribute={attribute} digest={digest}/>
        </div>
      </div>
      <div className="row align-items-center">
        <div className="col-md-1">Value:</div>
        <div className="col"><AttributeValue value={content.attribute.value} /></div>
      </div>
      <h2 className="mt-4">Containing collections:</h2>
      API URL: <Link to={api_url_list}>{api_url_list}</Link>
      <CollectionTable collections={content.results}  clipboard={false}/>
    </div>
  )
}


const copyToClipboard = async (text) => {
  console.log("Copying to clipboard")
  toast("Copied to clipboard", {autoClose: 1250, progress: undefined, hideProgressBar: true, pauseOnFocusLoss:false})
  return await navigator.clipboard.writeText(text)
}


const LinkedAttributeDigest = ({attribute, digest, clipboard=true}) => {
  return (<>
    <Link to={`/attribute/${attribute}/${digest}`} className="font-monospace">{digest}</Link> 
    { clipboard ? <img  role="button" src={copyToClipboardIcon} alt="Copy" width="30" className="copy-to-clipboard mx-2" onClick={() => copyToClipboard(digest)}/> : "" }
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
    for (let i = 0; i < seqColList.items.length; i++) {
      header_cells.push(<th key={"header_col_"+i} className='rotated-text'><div>{seqColList.items[i]}</div></th>)
    }
    let header_row = <tr><th></th>{header_cells}</tr>;

    let link_rows = [];
    for (let i = 0; i < seqColList.items.length; i++) {
      let link_cells = []
      link_cells.push(<th className="text-end" key={"header_row_"+i}><Link to={`/collection/${seqColList.items[i]}`}>{seqColList.items[i]}</Link></th>)
      for (let j = 0; j < seqColList.items.length; j++) {
        link_cells.push(
          <td key={i + "vs" + j} className="text-center">{ j == i ? "=" : <Link
            to={`/comparison/${seqColList.items[i]}/${seqColList.items[j]}`}
            key={`${seqColList.items[i]}-${seqColList.items[j]}`}
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

const SeqColList = ({collections}) => {
  const seqColList = collections || useLoaderData()

  return (<>
    <div>
      <h1>Sequence Collection List</h1>
      <ul>
        {seqColList.items.map((seqCol) => (
          <li key={seqCol}>
            <a href={`/collection/${seqCol}`}>{seqCol}</a>
          </li>
        ))}
      </ul>
      <CompareTable seqColList={seqColList}/>
    </div></>
  )
}

const CollectionTable = ({collections}) => {
  const seqColList = collections || useLoaderData()["items"]
  console.log("CollectionTable", seqColList)

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
    {seqColList.map((collection) => (
      <tr key={collection.digest}>
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





const router = createBrowserRouter([
  {
    path: "/",
    element: <App/>,
    children: [
      {
        path: "/",
        element: <SeqColList/>,
        loader: fetchSeqColList,
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
          return fetchAllCol(request.params.digest)
        }
      },
      {
        path: "/attribute/:attribute/:digest",
        element: <AttributeView/>,
        loader: (request) =>{ 
          console.log("params", request.params)
          return fetchAttribute(request.params.attribute, request.params.digest)
        
        }
      }
    ]
  },
]);


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
