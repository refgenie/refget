// const API_BASE = "http://127.0.0.1:8100"
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8100';
import copyToClipboardIcon from './assets/copy_to_clipboard.svg'
import barcodeIcon from './assets/barcode.svg'

import { toast } from 'react-toastify';

const copyToClipboard = async (text) => {
    console.log("Copying to clipboard")
    toast("Copied to clipboard", {autoClose: 1250, progress: undefined, hideProgressBar: true, pauseOnFocusLoss:false})
    return await navigator.clipboard.writeText(text)
}
  
const snakeToTitle = str => str
  .replace(/_/g, ' ')
  .replace(/\b\w/g, char => char.toUpperCase());

export { 
    API_BASE,
    barcodeIcon,
    copyToClipboard,
    copyToClipboardIcon,
    snakeToTitle
}