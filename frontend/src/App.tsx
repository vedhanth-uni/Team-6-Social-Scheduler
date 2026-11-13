import './App.css'
import { Routes, Route } from 'react-router';
import LoginPage from './LoginPage';
import DashboardPage from './DashboardPage';
import RequireAuth from './auth/RequireAuth';


function App() {
  return (
    <Routes>
      <Route path='/' element={<LoginPage/>}/>
      <Route path='/Dash' element={<RequireAuth><DashboardPage/></RequireAuth>}/>
    </Routes>
  )
}

export default App
