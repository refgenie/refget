import toast from 'react-hot-toast';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8100';
import copyToClipboardIcon from './assets/copy_to_clipboard.svg';
import barcodeIcon from './assets/barcode.svg';

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    toast.success('Digest copied!');
  } catch {
    toast.error('Failed to copy to clipboard');
  }
};

const snakeToTitle = (str: string) =>
  str.replace(/_/g, ' ').replace(/\b\w/g, (char: string) => char.toUpperCase());

// Human-readable byte size (e.g. 2.0 MB).
const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Unicode-safe base64 encoding
// Handles all Unicode characters including non-ASCII sequences
const encodeToBase64 = (str: string) => {
  return btoa(unescape(encodeURIComponent(str)));
};

// Unicode-safe base64 decoding
// Handles all Unicode characters including non-ASCII sequences
const decodeFromBase64 = (encoded: string) => {
  return decodeURIComponent(escape(atob(encoded)));
};

const encodeComparison = (input: unknown) => {
  let jsonString: string;

  if (typeof input === 'string') {
    try {
      JSON.parse(input);
      jsonString = input;
    } catch (error) {
      throw new Error('Invalid JSON string provided', { cause: error });
    }
  } else if (typeof input === 'object' && input !== null) {
    jsonString = JSON.stringify(input);
  } else {
    throw new Error('Input must be an object or valid JSON string');
  }

  return encodeToBase64(jsonString);
};

export {
  API_BASE,
  barcodeIcon,
  copyToClipboard,
  copyToClipboardIcon,
  snakeToTitle,
  formatBytes,
  encodeComparison,
  encodeToBase64,
  decodeFromBase64,
};
