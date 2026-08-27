/**
 * OPFS synchronous access handles.
 *
 * `createSyncAccessHandle` is Worker-only, so TypeScript declares it in
 * lib.webworker -- which this app cannot load alongside lib.dom. The VRS worker
 * needs it, so the surface it uses is declared here.
 */

interface FileSystemSyncAccessHandle {
  read(buffer: ArrayBufferView | ArrayBuffer, options?: { at?: number }): number;
  write(buffer: ArrayBufferView | ArrayBuffer, options?: { at?: number }): number;
  truncate(newSize: number): void;
  getSize(): number;
  flush(): void;
  close(): void;
}

interface FileSystemFileHandle {
  createSyncAccessHandle(): Promise<FileSystemSyncAccessHandle>;
}
