import React, { useEffect, useState } from 'react';

const RemoteSelector = () => {
  const [remotes, setRemotes] = useState([]);
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [sourceFiles, setSourceFiles] = useState([]);
  const [destinationFiles, setDestinationFiles] = useState([]);
  const [loadingSourceFiles, setLoadingSourceFiles] = useState(false);
  const [loadingDestinationFiles, setLoadingDestinationFiles] = useState(false);

  // Fetch remotes once on mount
  useEffect(() => {
    fetch('http://localhost:8000/rclone/remotes')
      .then(res => res.json())
      .then(data => setRemotes(data.remotes || []))
      .catch(err => console.error('Failed to fetch remotes:', err));
  }, []);

  // Fetch files when source changes
  useEffect(() => {
    if (!source) {
      setSourceFiles([]);
      return;
    }
    setLoadingSourceFiles(true);
    fetch(`http://localhost:8000/rclone/list?remote=${encodeURIComponent(source)}`)
      .then(res => res.json())
      .then(data => setSourceFiles(data))
      .catch(err => {
        console.error('Failed to fetch source files:', err);
        setSourceFiles([]);
      })
      .finally(() => setLoadingSourceFiles(false));
  }, [source]);

  // Fetch files when destination changes
  useEffect(() => {
    if (!destination) {
      setDestinationFiles([]);
      return;
    }
    setLoadingDestinationFiles(true);
    fetch(`http://localhost:8000/rclone/list?remote=${encodeURIComponent(destination)}`)
      .then(res => res.json())
      .then(data => setDestinationFiles(data))
      .catch(err => {
        console.error('Failed to fetch destination files:', err);
        setDestinationFiles([]);
      })
      .finally(() => setLoadingDestinationFiles(false));
  }, [destination]);

  const filteredDestinations = remotes.filter(r => r !== source);
  const filteredSources = remotes.filter(r => r !== destination);

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white shadow-lg rounded-xl">
      <h2 className="text-2xl font-semibold text-center mb-6">Select Source & Destination</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Source */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700">Source Remote</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Source</option>
            {filteredSources.map(remote => (
              <option key={remote} value={remote}>
                {remote}
              </option>
            ))}
          </select>
          {loadingSourceFiles && <p className="mt-2 text-sm text-gray-500">Loading files...</p>}
          {!loadingSourceFiles && sourceFiles.length > 0 && (
            <div className="mt-2 max-h-48 overflow-auto border border-gray-200 rounded p-2 bg-gray-50">
              <strong className="block mb-1">Source Files & Folders:</strong>
              <ul className="text-sm">
                {sourceFiles.map(file => (
                  <li key={file.ID} className={file.IsDir ? 'font-semibold' : ''}>
                    {file.Name} {file.IsDir ? '(Folder)' : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Destination */}
        <div>
          <label className="block mb-2 text-sm font-medium text-gray-700">Destination Remote</label>
          <select
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">Select Destination</option>
            {filteredDestinations.map(remote => (
              <option key={remote} value={remote}>
                {remote}
              </option>
            ))}
          </select>
          {loadingDestinationFiles && <p className="mt-2 text-sm text-gray-500">Loading files...</p>}
          {!loadingDestinationFiles && destinationFiles.length > 0 && (
            <div className="mt-2 max-h-48 overflow-auto border border-gray-200 rounded p-2 bg-gray-50">
              <strong className="block mb-1">Destination Files & Folders:</strong>
              <ul className="text-sm">
                {destinationFiles.map(file => (
                  <li key={file.ID} className={file.IsDir ? 'font-semibold' : ''}>
                    {file.Name} {file.IsDir ? '(Folder)' : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {source && destination && (
        <div className="mt-6 text-center text-green-700 font-semibold">
          ✅ Ready to transfer from <span className="underline">{source}</span> to <span className="underline">{destination}</span>
        </div>
      )}
    </div>
  );
};

export default RemoteSelector;
