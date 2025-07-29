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
      <h6 className="mb-2 mt-4 fw-medium">{attribute}</h6>
      <div className="row align-items-center home">
        <div className="col-md-1 text-muted">Digest:</div>
        <div className="col">
          <LinkedAttributeDigest attribute={attribute} digest={level1[attribute]}/>
        </div>
      </div>
      <div className="row align-items-center">
        <div className="col-md-1 text-muted">Value:</div>
        <div className="col">
          <AttributeValue value={level2[attribute]} />
        </div>
      </div>
      </div>
      )
    }
  
    return (
      <div>
        <h4 className='fw-light'>Sequence Collection: {digest}</h4>
        <p className="text-muted fs-6 mt-3">
          The <span className="font-monospace text-success">/collection</span> endpoint lets you retrieve
          the value of a sequence collection, in various forms, given its digest.
        </p>
        {/* <hr/> */}
        <h5 className='mt-4 pt-2'>Attribute View</h5>
        <p className="text-muted fs-6">
          Individual attributes have their own digests and values. 
          Click on a digest to see the <span className="font-monospace text-success">/attribute</span> page
          for that attribute value and find other collections with the same value.
        </p>
        {attribute_list_views}
        {/* <hr/> */}
        <h5 className='mt-4 pt-2'>Raw View</h5>
        <p className="text-muted fs-6">
          Sequence collections can be retrieved from the API in various forms.
          Choose among views below to see what is returned by the different endpoint options.
        </p>

        <div className='row g-3'>
          <div className='col-12'>
            <div className='card'>
              <div className='card-header d-flex justify-content-between align-items-center position-relative'>
                <button 
                  className='btn btn-link text-decoration-none p-0 flex-grow-1 text-start text-black stretched-link'
                  type='button' 
                  data-bs-toggle='collapse' 
                  data-bs-target='#collapseLevel1' 
                  aria-expanded='true' 
                  aria-controls='collapseLevel1'
                >
                  <h6 className='mb-0'>Level 1: {urls['level1']}</h6>
                </button>
                <a 
                  className='btn btn-secondary btn-sm' 
                  href={API_BASE+urls['level1']}
                  target='_blank' 
                  rel='noopener noreferrer'
                  style={{zIndex: 999}}
                >
                  <i className='bi bi-box-arrow-up-right me-2' />API
                </a>
              </div>
              <div id='collapseLevel1' className='collapse show'>
                <div className='card-body'>
                  <pre className='card card-body bg-light mb-0'>{JSON.stringify(level1, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>

          <div className='col-12'>
            <div className='card'>
              <div className='card-header d-flex justify-content-between align-items-center position-relative'>
                <button 
                  className='btn btn-link text-decoration-none p-0 flex-grow-1 text-start text-black stretched-link'
                  type='button' 
                  data-bs-toggle='collapse' 
                  data-bs-target='#collapseLevel2' 
                  aria-expanded='false' 
                  aria-controls='collapseLevel2'
                >
                  <h6 className='mb-0'>Level 2: {urls['level2']}</h6>
                </button>
                <a 
                  className='btn btn-secondary btn-sm' 
                  href={API_BASE+urls['level2']}
                  target='_blank' 
                  rel='noopener noreferrer'
                  style={{zIndex: 999}}
                >
                  <i className='bi bi-box-arrow-up-right me-2' />API
                </a>
              </div>
              <div id='collapseLevel2' className='collapse'>
                <div className='card-body'>
                  <pre className='card card-body bg-light mb-0'>{JSON.stringify(level2, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>

          <div className='col-12'>
            <div className='card'>
              <div className='card-header d-flex justify-content-between align-items-center position-relative'>
                <button 
                  className='btn btn-link text-decoration-none p-0 flex-grow-1 text-start text-black stretched-link'
                  type='button' 
                  data-bs-toggle='collapse' 
                  data-bs-target='#collapseUncollated' 
                  aria-expanded='false' 
                  aria-controls='collapseUncollated'
                >
                  <h6 className='mb-0'>Uncollated: {urls['uncollated']}</h6>
                </button>
                <a 
                  className='btn btn-secondary btn-sm' 
                  href={API_BASE+urls['uncollated']}
                  target='_blank' 
                  rel='noopener noreferrer'
                  style={{zIndex: 999}}
                >
                  <i className='bi bi-box-arrow-up-right me-2' />API
                </a>
              </div>
              <div id='collapseUncollated' className='collapse'>
                <div className='card-body'>
                  <pre className='card card-body bg-light mb-0'>{JSON.stringify(uncollated, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>


      </div>
    )
  }
  
export { CollectionView }

