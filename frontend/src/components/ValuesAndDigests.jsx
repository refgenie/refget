import { Link } from "react-router-dom";
import { copyToClipboardIcon, copyToClipboard } from "../utilities";

const AttributeValue = ({value}) => {
    console.log("AttributeValue", value)
    if (value === null) {
        return(<pre className="text-secondary m-0 p-2 border border-muted"><code>null</code></pre>)
    }
    return(<pre className="text-secondary m-0 p-2 border border-muted"><code>{value.join(",")}</code></pre>)
}

const LinkedAttributeDigest = ({attribute, digest, clipboard=true}) => {
    return (<>
        <Link to={`/attribute/${attribute}/${digest}`} className="font-monospace">{digest}</Link> 
        { clipboard ? <img  role="button" src={copyToClipboardIcon} alt="Copy" width="30" className="copy-to-clipboard mx-2" onClick={() => copyToClipboard(digest)}/> : "" }
        </>
    )
}
  
const LinkedCollectionDigest = ({digest, clipboard=true}) => {
    return (<>
      <Link to={`/collection/${digest}`} className="font-monospace">{digest}</Link> 
      { clipboard ? <img role="button" src={copyToClipboardIcon} alt="Copy" width="30" className="copy-to-clipboard mx-2" onClick={ () => navigator.clipboard.writeText(digest)}/> : "" }
      </>
    )
  }
  

export {
    AttributeValue,
    LinkedAttributeDigest,
    LinkedCollectionDigest
}
