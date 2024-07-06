import { Link, useLoaderData, useParams } from "react-router-dom"
import { useState } from 'react'
import { API_BASE } from '../utilities.jsx'
import { AttributeValue, LinkedAttributeDigest } from '../components/Attributes.jsx'

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
      attribute_list_views.push(
      <div key={attribute}>
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
      </div>
      )
    }
  
    return (
      <div>
        <h2>Sequence Collection: {digest}</h2>
        <hr/>
          <h2>API URLs</h2>
        <ul>
          <li>Level 1: <Link to={api_url_level1}>{api_url_level1}</Link></li>
          <li>Level 2: <Link to={api_url_level2}>{api_url_level2}</Link></li>
          <li>Uncollated: <Link to={api_url_uncollated}>{api_url_uncollated}</Link></li>
        </ul>
        <hr/>
        <h2>Attribute view: </h2>
        {attribute_list_views}
        <hr/>
        <h2>Raw view:</h2>
        <h3>Level 1:</h3>
        <pre className="card card-body bg-light">{JSON.stringify(level1, null, 2)}</pre>
        <h3>Level 2:</h3>
        <pre className="card card-body bg-light">{JSON.stringify(level2, null, 2)}</pre>

      </div>
    )
  }
  
export { CollectionView }