import toast from 'react-hot-toast';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8100';
import copyToClipboardIcon from './assets/copy_to_clipboard.svg';
import barcodeIcon from './assets/barcode.svg';

const copyToClipboard = async (text) => {
  toast.success('Copied to clipboard!');
  return await navigator.clipboard.writeText(text);
};

const snakeToTitle = (str) =>
  str.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const encodeComparison = (input) => {
  let jsonString;

  if (typeof input === 'string') {
    try {
      JSON.parse(input);
      jsonString = input;
    } catch (error) {
      throw new Error('Invalid JSON string provided');
    }
  } else if (typeof input === 'object' && input !== null) {
    jsonString = JSON.stringify(input);
  } else {
    throw new Error('Input must be an object or valid JSON string');
  }

  return btoa(jsonString);
};

export {
  API_BASE,
  barcodeIcon,
  copyToClipboard,
  copyToClipboardIcon,
  snakeToTitle,
  encodeComparison,
};
