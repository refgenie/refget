import { PangenomeList } from '../components/ObjectLists.jsx'
import { CollectionList } from '../components/ObjectLists.jsx'
import { Link } from "react-router-dom";
import { useLoaderData } from "react-router-dom";
import { AttributeList } from '../components/ObjectLists';


const HomePage = () => {
    const loaderData = useLoaderData()
    console.log("HomePage loaderData ", loaderData)
    const collections = loaderData[0]
    const pangenomes = loaderData[1]
    const name_length_pairs = loaderData[2]
  
    const PangenomeExamplesList = () => {
      if (pangenomes && pangenomes.results && pangenomes.results.length > 0) {
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

        <div className="d-flex justify-content-end float-end">
          <div className="card">
            <div className="card-body">
              This server is hosting <b>{collections?.pagination?.total ?? 0}</b> collections.
            </div>
          </div>
        </div>


        <p>Welcome to the Refget Sequence Collections demo service!
          This landing page provides a way to explore the data in the server.
          You can go straight to the API itself using the <b>API Docs</b> link in the title bar.
          Or, you can check out a few examples below. Here are some ways to browse:
        </p>

  

        <h5>1. View and compare the demo sequence collections:</h5>
        <p className="text-muted fs-6">
          This service includes several small demo collections. This page will show you 
          comparisons between them:
        </p>
  
        <ul>
          <li><Link to="/demo">Demo of collection comparisons</Link></li>
        </ul>
        
        <h5 className="mt-4">2. Example Sequence Collections on this server:</h5>
        <p className="text-muted fs-6">
          This uses the <span className="font-monospace text-success">/list/collections</span> endpoint,
          which provides a paged list of all collections hosted by this server.
        </p>
  
        <CollectionList collections={collections}/>

        <h5 className="mt-4">3. Human Reference genomes available on this server:</h5>
        
        <ul>
          <li><Link to="/human">Human reference genomes</Link></li>
        </ul>



        <h5 className="mt-4">4. Human Pangenome Reference Consortium genomes available on this server:</h5>
        
        <ul>
          <li><Link to="/hprc">HPRC genomes</Link></li>
        </ul>
        <PangenomeExamplesList/>

        <h5 className="mt-4">4. List of name_length_pairs on this server:</h5>
        <p className="text-muted fs-6">
        The <span className="font-monospace text-success">/list/attributes</span> endpoint lets you retrieve
        a list of all the values of a particular attribute hosted by this server.
        </p>
        <AttributeList attributeName="name_length_pairs" attributeDigests={name_length_pairs}/>


      </div>
    )
  }

  export { HomePage }