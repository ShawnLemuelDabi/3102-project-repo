import { useState, useEffect } from 'react'
import { Storage } from 'aws-amplify'

function App() {
  const [images, setImages] = useState([])
  useEffect(() => {
    fetchImages()
  }, [])
  async function fetchImages() {
    let imageKeys = await Storage.list('')
    imageKeys = await Promise.all(imageKeys.map(async k => {
      const key = await Storage.get(k.key)
      return key
    }))
    console.log('imageKeys: ', imageKeys)
    setImages(imageKeys)
  }
  async function onChange(e) {
    const file = e.target.files[0];
    const result = await Storage.put(file.name, file, {
      contentType: 'image/png'
    })
    console.log({ result })
    fetchImages()
  }
  return (
    <div className="App">
      <h1>Test</h1>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {
          images.map(image => (
            <img
              src={image}
              key={image}
              style={{width: 500, height: 300}}
            />
          ))
        }
      </div>
      <input
        type="file"
        onChange={onChange}
      />
    </div>
  );
}

export default App;