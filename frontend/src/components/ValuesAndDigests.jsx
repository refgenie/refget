import { Link } from 'react-router-dom';
import {
  barcodeIcon,
  copyToClipboardIcon,
  copyToClipboard,
} from '../utilities';

const AttributeValue = ({ value }) => {
  console.log('AttributeValue', value);
  console.log('typeof', typeof value);
  if (value === null) {
    return (
      <pre className='m-0 p-2 border border-muted'>
        <code>null</code>
      </pre>
    );
  }
  if (Array.isArray(value)) {
    return (
      <pre className='m-0 p-2 border border-muted'>
        <code>{value.map((x) => JSON.stringify(x)).join(',')}</code>
      </pre>
    );
  }
  return (
    <pre className=' m-0 p-2 border border-muted'>
      <code>{value}</code>
    </pre>
  );
};

const LinkedAttributeDigest = ({ attribute, digest, clipboard = true }) => {
  return (
    <>
      <img src={barcodeIcon} alt='Barcode' width='30' className='mx-1' />
      <Link
        to={`/attribute/${attribute}/${digest}`}
        className='font-monospace small'
      >
        {digest}
      </Link>
      {clipboard ? (
        <img
          role='button'
          src={copyToClipboardIcon}
          alt='Copy'
          width='24'
          className='copy-to-clipboard mx-2'
          onClick={() => copyToClipboard(digest)}
        />
      ) : (
        ''
      )}
    </>
  );
};

const LinkedCollectionDigest = ({ digest, clipboard = true }) => {
  return (
    <>
      <img src={barcodeIcon} alt='Barcode' width='30' className='mx-1' />
      <Link to={`/collection/${digest}`} className='font-monospace small'>
        {digest}
      </Link>
      {clipboard ? (
        <img
          role='button'
          src={copyToClipboardIcon}
          alt='Copy'
          width='24'
          className='copy-to-clipboard mx-2'
          onClick={() => navigator.clipboard.writeText(digest)}
        />
      ) : (
        ''
      )}
    </>
  );
};

export { AttributeValue, LinkedAttributeDigest, LinkedCollectionDigest };
