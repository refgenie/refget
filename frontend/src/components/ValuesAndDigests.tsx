import { Link } from 'react-router-dom';
import {
  barcodeIcon,
  copyToClipboardIcon,
  copyToClipboard,
} from '../utilities';
import { useExplorerApi } from '../hooks/useExplorerApi';
import { attributePath, collectionPath } from '../utils/explorerLinks';

interface AttributeValueProps {
  /** A level-2 attribute value: an array of items, a scalar, or null. */
  value: unknown;
}

const AttributeValue = ({ value }: AttributeValueProps) => {
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
    <pre className='m-0 p-2 border border-muted'>
      <code>{String(value)}</code>
    </pre>
  );
};

interface DigestLinkProps {
  digest: string;
  /** Show the click-to-copy button next to the digest. */
  clipboard?: boolean;
}

const LinkedAttributeDigest = ({
  attribute,
  digest,
  clipboard = true,
  transient = false,
}: DigestLinkProps & {
  attribute: string;
  /** A transient attribute has no /attribute page, so show the digest unlinked. */
  transient?: boolean;
}) => {
  const apiUrl = useExplorerApi();
  return (
    <>
      <img src={barcodeIcon} alt='Barcode' width='30' className='mx-1' />
      {transient ? (
        <span className='font-mono text-sm'>{digest}</span>
      ) : (
        <Link
          to={attributePath(attribute, digest, apiUrl)}
          className='font-mono text-sm'
        >
          {digest}
        </Link>
      )}
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

const LinkedCollectionDigest = ({ digest, clipboard = true }: DigestLinkProps) => {
  const apiUrl = useExplorerApi();
  return (
    <>
      <img src={barcodeIcon} alt='Barcode' width='30' className='mx-1' />
      <Link to={collectionPath(digest, apiUrl)} className='font-mono text-sm'>
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

export { AttributeValue, LinkedAttributeDigest, LinkedCollectionDigest };
