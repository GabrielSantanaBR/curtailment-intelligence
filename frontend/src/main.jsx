import React,{useEffect,useState} from 'react';
import{createRoot}from'react-dom/client';
import'./styles.css';
function App(){const[overview,setOverview]=useState(null);useEffect(()=>{fetch('http://localhost:8000/api/v1/overview').then(r=>r.json()).then(setOverview)},[]);return <main><p>Curtailment Intelligence / React workspace</p><h1>{overview?`${overview.curtailed_mwh.toLocaleString()} MWh`:"Conectando..."}</h1><span>Base React pronta para evolução do DEV Front.</span></main>};createRoot(document.getElementById('root')).render(<App/>);
