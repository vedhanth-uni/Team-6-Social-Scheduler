import './App.css'
import { Routes, Route } from 'react-router';
import LoginPage from './LoginPage';
import DashboardPage from './DashboardPage';


function App() {
  return (
    <Routes>
      <Route path='/' element={<LoginPage/>}/>
      <Route path='/Dash' element={<DashboardPage/>}/>
    </Routes>
  )
}

export default App
