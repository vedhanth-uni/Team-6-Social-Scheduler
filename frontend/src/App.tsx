import './App.css'
import { Routes, Route } from 'react-router';
import LoginPage from './LoginPage';
import DashboardPage from './DashboardPage';
import FeedPage from './FeedPage';


function App() {
  return (
    <Routes>
      <Route path='/' element={<LoginPage/>}/>
      <Route path='/Dash' element={<DashboardPage/>}/>
      <Route path='/Feed' element={<FeedPage/>}/>
    </Routes>
  )
}

export default App
