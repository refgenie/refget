// This is a utilities module (no React components), so the Fast Refresh
// "only export components" rule does not apply. Disabling it here avoids an
// invasive rename of utilities.jsx -> utilities.js across ~15 import sites.
/* eslint-disable react-refresh/only-export-components */
import toast from 'react-hot-toast';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8100';
import copyToClipboardIcon from './assets/copy_to_clipboard.svg';
import barcodeIcon from './assets/barcode.svg';

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    toast.success('Digest copied!');
  } catch {
    toast.error('Failed to copy to clipboard');
  }
};

const snakeToTitle = (str) =>
  str.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

// Human-readable byte size (e.g. 2.0 MB).
const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Unicode-safe base64 encoding
// Handles all Unicode characters including non-ASCII sequences
const encodeToBase64 = (str) => {
  return btoa(unescape(encodeURIComponent(str)));
};

// Unicode-safe base64 decoding
// Handles all Unicode characters including non-ASCII sequences
const decodeFromBase64 = (encoded) => {
  return decodeURIComponent(escape(atob(encoded)));
};

const encodeComparison = (input) => {
  let jsonString;

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
