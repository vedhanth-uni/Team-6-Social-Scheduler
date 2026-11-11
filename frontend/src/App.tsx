import './App.css'
import { Routes, Route } from 'react-router';
import LoginPage from './LoginPage';
import DashboardPage from './DashboardPage';
import FriendRespondPage from './FriendRespondPage';


function App() {
  return (
    <Routes>
      <Route path='/' element={<LoginPage/>}/>
      <Route path='/Dash' element={<DashboardPage/>}/>
      <Route path='/friends/respond' element={<FriendRespondPage/>}/>
    </Routes>
  )
}

export default App
