import { useState, useCallback } from 'react';

// No max file size - streaming handles any size
const WARN_FILE_SIZE = 500 * 1024 * 1024; // 500MB - warn but allow

export default function FastaDropzone({ onFileSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false);

  const validateFile = (file) => {
    // Check extension
    const validExts = ['.fa', '.fasta', '.fna', '.fa.gz', '.fasta.gz', '.fna.gz'];
    const hasValidExt = validExts.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      return 'Please upload a FASTA file (.fa, .fasta, .fna, or gzipped)';
    }
    return null;
  };

  const handleFile = useCallback((file) => {
    const error = validateFile(file);
    if (error) {
      alert(error);
      return;
    }

    // Warn about large files
    if (file.size > WARN_FILE_SIZE) {
      const sizeGB = (file.size / 1e9).toFixed(1);
      const msg = `This file is ${sizeGB}GB. Processing will use streaming and may take a while. Continue?`;
      if (!confirm(msg)) {
        return;
      }
    }

    onFileSelected(file);
  }, [onFileSelected]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer?.files[0];
    if (file) handleFile(file);
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`fasta-dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
    >
      <input
        type="file"
        accept=".fa,.fasta,.fna,.gz"
        onChange={handleChange}
        disabled={disabled}
        id="fasta-file-input"
      />
      <label htmlFor="fasta-file-input">
        <i className="bi bi-file-earmark-arrow-up"></i>
        <span>Drop FASTA file here or click to browse</span>
        <small>Supports .fa, .fasta, .fna (plain or gzipped) - any size</small>
      </label>
    </div>
  );
}
