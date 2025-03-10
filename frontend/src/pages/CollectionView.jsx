import { Link, useLoaderData, useParams } from "react-router-dom"
import { useState } from 'react'
import { API_BASE } from '../utilities.jsx'
import { AttributeValue, LinkedAttributeDigest } from '../components/ValuesAndDigests.jsx'

const CollectionView = (params) => {
    const collection = useLoaderData()
    const [collectionRepresentation, setCollectionRepresentation] = useState(null)
    const { digest } = useParams()
    console.log("CollectionView", collection)
    
    let level1 = collection[0]
    let level2 = collection[1]
    let uncollated = collection[2]

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

    const urls = {
      level1: `/collection/${digest}?level=1`,
      level2: `/collection/${digest}?level=2`,
      uncollated: `/collection/${digest}?collated=false`
    }

    let attribute_list_views = []
    for ( let attribute in level2) {
      attribute_list_views.push(
      <div key={attribute}>
      <h5 className="mb-2 mt-3">{attribute}</h5>
      <div className="row align-items-center">
        <div className="col-md-1 text-secondary">Digest:</div>
        <div className="col">
          <LinkedAttributeDigest attribute={attribute} digest={level1[attribute]}/>
        </div>
      </div>
      <div className="row align-items-center">
        <div className="col-md-1 text-secondary">Value:</div>
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
        <p className="text-muted fs-6">
          The <span className="font-monospace text-success">/collection</span> endpoint lets you retrieve
          the value of a sequence collection, in various forms, given its digest.
        </p>
        <hr/>
        <h2>Attribute view: </h2>
        <p className="text-muted fs-6">
          Individual attributes have their own digests and values. 
          Click on a digest to see the <span className="font-monospace text-success">/attribute</span> page
          for that attribute value and find other collections with the same value.
        </p>
        {attribute_list_views}
        <hr/>
        <h2>Raw view:</h2>
        <p className="text-muted fs-6">
          Sequence collections can be retrieved from the API in various forms.
          Choose among views below to see what is returned by the different endpoint options.
        </p>
        <div className="accordion" id="accordionExample">
        <div className="accordion-item">
          <h2 className="accordion-header">
            <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
            Level 1:  {urls["level1"]}
            </button>
          </h2>
          <div id="collapseOne" className="accordion-collapse collapse show" data-bs-parent="#accordionExample">
            <div className="accordion-body">
              API URL: <Link to={API_BASE+urls["level1"]}>{urls["level1"]}</Link>
              <pre className="card card-body bg-light">{JSON.stringify(level1, null, 2)}</pre>
           </div>
          </div>
        </div>
        <div className="accordion-item">
          <h2 className="accordion-header">
            <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
              Level 2: {urls["level2"]}
            </button>
          </h2>
          <div id="collapseTwo" className="accordion-collapse collapse" data-bs-parent="#accordionExample">
            <div className="accordion-body">
             API URL: <Link to={API_BASE+urls["level2"]}>{urls["level2"]}</Link>
            <pre className="card card-body bg-light">{JSON.stringify(level2, null, 2)}</pre>
            </div>
          </div>
        </div>
        <div className="accordion-item">
          <h2 className="accordion-header">
            <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
              Uncollated: {urls["uncollated"]}
            </button>
          </h2>
          <div id="collapseThree" className="accordion-collapse collapse" data-bs-parent="#accordionExample">
            <div className="accordion-body">
            Uncollated: <Link to={API_BASE+urls["uncollated"]}>{urls["uncollated"]}</Link>
            <pre className="card card-body bg-light">{JSON.stringify(uncollated, null, 2)}</pre>
            </div>
          </div>
        </div>
      </div>


      </div>
    )
  }
  
export { CollectionView }

